import json
import multiprocessing
import random
import requests
from concurrent.futures import ThreadPoolExecutor


from zpywallet.errors import NetworkException
from zpywallet.generated import wallet_pb2

from zpywallet.mempool.cache import SQLTransactionStorage, DatabaseError


def transform_and_sort_transactions(data):
    transformed_data = [
        {**value, "txid": txid} for txid, value in data["result"].items()
    ]
    sorted_data = sorted(
        transformed_data, key=lambda x: x["fees"]["modified"] / x["vsize"], reverse=True
    )
    return sorted_data


class BTCLikeMempool:
    """Holds the transactions of Bitcoin-like blockchains inside the mempool.
    There should only be one mempool class for each coin running in the entire
    application.

    The performance of this class heavily depends on the network speed and CPU
    speed of the node as well as the number of threads available, the size of the RPC
    batch work queue specified in the constructor, and the amount of transactions in
    megabytes you are trying to fetch at once.

    Additionally, the number of transactions returned depends on the number of
    transactions in the mempool itself and how well-connected the node is to other
    nodes. The longer you run your node and the more peers it has, the faster
    the mempool fills up with thransactions.

    If you intend to use the mempool to track pending payments, it is recommended
    to update it once every 10 to 60 seconds for optimal user experience. However,
    if this mempool class is empty, it can take several minutes to fill it with the
    current mempool. As a result, you should do this while your app is initializing
    in order to avoid stuck processing workflows caused by slow mempool initialization.

    The mempool class caches existing unconfirmed tranasctions so that they do not have
    to be fetched a second time, which should greatly improve performance and reduce
    waiting times during status updates. However, because the memory footprint of
    the unconfirmed transactions can take a few hundred megabytes per future block,
    it is strongly recommended to offload the lower-fee transactions to a database
    or to the disk.

    With that being said, attempting to load dozens of blocks into memory with this
    class will most likely cause your application to run out of memory. Additionally,
    this class does not work well with nodes running behind web servers that use
    rate limiting.

    Considering all this, we recommend using this class only if you are running a
    dedicated full node, if you only want to fetch only the highest few megabytes'
    worth of mempool transactions, or if you have a database available for storage.
    """

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        # Of course this is an unconfirmed transaction.
        # Hence it is also not a coinbase transaction.
        new_element.confirmed = False
        new_element.txid = element["txid"]

        for vin in element["vin"]:
            if "txid" not in vin.keys():
                continue
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = vin["txid"]
            txinput.index = vin["vout"]
            # To fill in the amount, we have to get the other transaction id.
            # But we can do that all at once in one RPC call.
            # So we will cache them to retrieve later.
            self.txos.append(txinput.txid)

        for vout in element["vout"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"] * 1e8)
            txoutput.index = vout["n"]
            if "address" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["address"]
            elif "addresses" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["addresses"][0]

        # We have to save the vsize somewhere because we'll need it later
        new_element.btclike_transaction.fee = element["vsize"]
        return new_element

    def _post_clean_tx(self, new_element, sql_transaction_storage):
        for txinput in new_element.btclike_transaction.inputs:
            fine_rawtx = sql_transaction_storage.get_rawtx(txinput.txid)
            if fine_rawtx is None:
                return None  # maybe processing error.
            txinput.amount = fine_rawtx.btclike_transaction.outputs[
                txinput.index
            ].amount
            txinput.address = fine_rawtx.btclike_transaction.outputs[
                txinput.index
            ].address

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])

        new_element.total_fee = total_inputs - total_outputs

        # The vsize was stored in the fee field.
        new_element.btclike_transaction.fee = int(
            (total_inputs - total_outputs) // new_element.btclike_transaction.fee
        )
        new_element.fee_metric = wallet_pb2.VBYTE

        return new_element

    def __init__(self, **kwargs):
        self.rpc_url = kwargs.get("url")
        self.rpc_user = kwargs.get("user")
        self.rpc_password = kwargs.get("password")
        self.max_workers = kwargs.get("max_workers") or 150
        self.max_batch = kwargs.get("max_batch") or 1000
        self.rps = kwargs.get("rps") or 4
        self.future_blocks_min = kwargs.get("future_blocks_min") or 0
        self.future_blocks_max = kwargs.get("future_blocks_max") or 1
        self.full_transactions = kwargs.get("full_transactions") or True
        self.db_connection_parameters = kwargs.get("db_connection_parameters")
        self.transactions = []
        self.in_mempool = []
        self.txos = []
        self.raw_txos = {}

    def _send_rpc_request(self, method, params=None):
        payload = {
            "method": method,
            "params": params or [],
            "jsonrpc": "2.0",
            "id": random.randint(1, 999999),
        }
        try:
            response = requests.post(
                self.rpc_url,
                auth=(
                    (self.rpc_user, self.rpc_password)
                    if self.rpc_user and self.rpc_password
                    else None
                ),
                json=payload,
                timeout=86400,
            )
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")

        # Certain nodes which are placed behind web servers or Cloudflare will
        # configure rate limits and return some HTML error page if we go over that.
        # Zpywallet is not designed to handle such content so we check for it first.
        # If you are using the full node facilities, you are recommended to connect
        # to your own node and not to a public one, for this reason.
        try:
            j = response.json()
        except json.decoder.JSONDecodeError:
            raise NetworkException("Internal RPC node error - expected JSON output")

        if "result" not in j.keys():
            raise NetworkException("Failed to get result")
        return j

    def _send_batch_rpc_request(self, reqs):
        payload = []
        for method, params in reqs:
            payload.append(
                {
                    "method": method,
                    "params": params or [],
                    "jsonrpc": "2.0",
                    "id": random.randint(1, 999999),
                }
            )

        try:
            # Requests session is not needed for the full node but we can use it
            # for the other providers in the future.
            response = requests.post(
                self.rpc_url,
                auth=(
                    (self.rpc_user, self.rpc_password)
                    if self.rpc_user and self.rpc_password
                    else None
                ),
                json=payload,
                timeout=86400,
            )
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")

        # Certain nodes which are placed behind web servers or Cloudflare will
        # configure rate limits and return some HTML error page if we go over that.
        # Zpywallet is not designed to handle such content so we check for it first.
        # If you are using the full node facilities, ou are recommended to connect
        # to your own node and not to a public one, for this reason.
        try:
            jj = response.json()
        except json.decoder.JSONDecodeError:
            print(response.text)
            raise NetworkException("Internal RPC node error - expected JSON output")

        for j in jj:
            if "result" not in j.keys():
                # Silently ignore the error since it only occurs in the case
                # of bad requests, replaced transactions, and so on which
                # either do not happen in this code or (in the case of RBF
                # replacement) must be ignored.
                # If the workflow is correct then either all of the results
                # will be successful or they will all fail. No in-between.
                # raise NetworkException("Failed to get result")
                continue
            yield j

    def _get_block_height(self):
        response = self._send_rpc_request("getblockchaininfo")
        try:
            return response["result"]["blocks"]
        except Exception as e:
            raise NetworkException(f"Failed to make RPC Call: {str(e)}")

    # Internal methods are ran in a separate process which allows the OS
    # to properly garbage collect the memory, as Python leaves a large footprint
    # behind.
    def _internal_mempool_fetch(self):
        res = self._send_rpc_request("getrawmempool", [True])
        sorted_transactions = transform_and_sort_transactions(res)
        return [tx["txid"] for tx in sorted_transactions]

    def _internal_pass_1(self, transaction_batch):
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)
        sql_transaction_storage.connect()
        try:
            # The first pass will be to delete the confirmed transactions inside the DB
            # if applicable.
            txids = transaction_batch
            all_txids = sql_transaction_storage.all_txids()
            for saved_txid in all_txids:
                if saved_txid not in txids:
                    sql_transaction_storage.delete_transaction(saved_txid)

            sql_transaction_storage.wipeout_reftxos()
            sql_transaction_storage.commit()

            # The second pass will be to create a copy of the mempool transactions
            # without the ones we already have stored inside the list or DB.
            new_txids = list(set(txids) - set(all_txids))

            new_txid_batches = [
                [t for t in new_txids[i : i + self.max_batch]]
                for i in range(0, len(new_txids), self.max_batch)
            ]
            return new_txid_batches

        except Exception as e:
            sql_transaction_storage.rollback()
            raise e

    def _internal_pass_2(self, transaction_batch):
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)
        sql_transaction_storage.connect()
        try:
            txids = transaction_batch
            # Next we are going to yield new mempool transactions that we don't have
            # Confirmed mempool transactions are dropped by this method and the one above.
            txid_batches = [
                txids[i : i + self.max_workers]
                for i in range(0, len(txids), self.max_workers)
            ]

            transaction_ids = [tx.txid for tx in self.transactions]

            with ThreadPoolExecutor(max_workers=self.rps) as executor:
                futures = [
                    executor.submit(self._process_transaction, txes, transaction_ids)
                    for txes in txid_batches
                ]
                temp_transactions = []
                for future in futures:
                    temp_transactions.extend(future.result())

            # If we only need to know information about the outputs and not the inputs
            # (e.g. payment processing) then we can skip the very expensive process of
            # resolving txins.
            if not self.full_transactions:
                for tx in temp_transactions:
                    tx.total_fee = 0  # Because this is actually the (v)size
                    sql_transaction_storage.store_transaction(tx)
                    for i in range(len(tx.btclike_transaction.outputs)):
                        sql_transaction_storage.store_txo0(tx, i)
                sql_transaction_storage.commit()
                return

            # Otherwise we have to get all of the input txids in one swoop so we can
            # finish processing the mempool transactions.
            txid_batches = [
                self.txos[i : i + self.max_workers]
                for i in range(0, len(self.txos), self.max_workers)
            ]
            with ThreadPoolExecutor(max_workers=self.rps) as executor:
                futures = [
                    executor.submit(self._postprocess_transaction, txes)
                    for txes in txid_batches
                ]
                for future in futures:
                    results = future.result()
                    for txid, result in results.items():
                        try:
                            sql_transaction_storage.store_txo1(txid, result)
                        except DatabaseError:
                            pass

            self.txos = []
            for i in range(len(temp_transactions) - 1, -1, -1):
                temp_transaction = temp_transactions[i]
                new_transaction = self._post_clean_tx(
                    temp_transaction, sql_transaction_storage
                )
                if new_transaction is not None:
                    sql_transaction_storage.store_transaction(new_transaction)
                    for j in range(len(new_transaction.btclike_transaction.inputs)):
                        sql_transaction_storage.store_txo0(
                            new_transaction, j, output=False
                        )
                    for j in range(len(new_transaction.btclike_transaction.outputs)):
                        sql_transaction_storage.store_txo0(new_transaction, j)
                del temp_transactions[i]
            sql_transaction_storage.wipeout_reftxos()
            sql_transaction_storage.commit()
        except Exception as e:
            sql_transaction_storage.rollback()
            raise e

    def _get_raw_mempool(self):
        with multiprocessing.Pool(1) as pool:
            transaction_batches = pool.apply(self._internal_mempool_fetch)

        new_txid_batches = self._internal_pass_1(transaction_batches)

        for transaction_batch in new_txid_batches:
            self._internal_pass_2(transaction_batch)

    def _postprocess_transaction(self, txes):
        res = self._send_batch_rpc_request(
            [("getrawtransaction", [tx, True]) for tx in txes]
        )

        input_transactions = {}
        for r in res:
            if type(r) is dict and "result" in r.keys():
                input_transactions[r["result"]["txid"]] = self._clean_tx(
                    r["result"]
                ).SerializeToString()

        return input_transactions

    def _process_transaction(self, txes, txids):
        txes = [tx for tx in txes if tx not in txids]
        if not txes:
            return []
        raw_transactions = [
            r
            for r in self._send_batch_rpc_request(
                [("getrawtransaction", [tx, 1]) for tx in txes]
            )
        ]
        temp_transactions = []
        for raw_transaction in raw_transactions:
            raw_transaction = raw_transaction["result"]
            if not raw_transaction:
                # Perhaps it has been replaced
                continue
            if "vin" not in raw_transaction.keys():
                # Ignore coinbase transactions
                continue
            temp_transactions.append(self._clean_tx(raw_transaction))

        return temp_transactions

    def get_raw_mempool(self):
        self._get_raw_mempool()
        return []