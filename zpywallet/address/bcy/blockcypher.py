import requests
import time
import datetime

from ...errors import NetworkException
from ...generated import wallet_pb2

from functools import reduce


def deduplicate(elements):
    return reduce(lambda re, x: re + [x] if x not in re else re, elements, [])


def convert_to_utc_timestamp(date_string, format_string="%Y-%m-%dT%H:%M:%SZ"):
    date_object = datetime.datetime.strptime(date_string, format_string)
    utc_date = date_object.astimezone(datetime.timezone.utc)
    return int(utc_date.timestamp())


class BlockcypherAddress:
    """
    A class representing a list of Blockcypher Testnet addresses.

    This class allows you to retrieve the balance and transaction history of a
    Blockcypher Testnet address using the Blockcypher API.
    """

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]

        if "block_height" not in element.keys():
            new_element.confirmed = False
        elif element["block_height"] == -1:
            new_element.confirmed = False
        elif element["block_index"] == 0:  # coinbase transaction
            new_element.confirmed = True
            new_element.height = 0
        else:
            new_element.confirmed = True
            new_element.height = element["block_height"]

        if "confirmed" in element.keys():
            new_element.timestamp = convert_to_utc_timestamp(
                element["confirmed"].split(".")[0].split("Z")[0], "%Y-%m-%dT%H:%M:%S"
            )

        for vin in element["inputs"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = "" if "prev_hash" not in vin.keys() else vin["prev_hash"]
            txinput.index = vin["output_index"]
            txinput.amount = (
                0 if "output_value" not in vin.keys() else int(vin["output_value"])
            )

        i = 0
        for vout in element["outputs"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"])
            txoutput.index = i
            i += 1
            if vout["addresses"]:
                txoutput.address = vout["addresses"][0]
            txoutput.spent = "spent_by" in vout.keys()

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        size_element = (
            element["vsize"] if "vsize" in element.keys() else element["size"]
        )
        new_element.btclike_transaction.fee = int(new_element.total_fee // size_element)
        new_element.fee_metric = wallet_pb2.BYTE

        return new_element

    def __init__(
        self,
        addresses,
        request_interval=(3, 1),
        transactions=None,
        api_key=None,
        **kwargs,
    ):
        """
        Initializes an instance of the BlockcypherAddress class.

        Args:
            addresses (list): A list of human-readable Blockcypher Testnet addresses.
            api_key (str): The API key for accessing the Blockcypher API.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.addresses = addresses
        self.api_key = api_key
        self.requests, self.interval_sec = request_interval
        self.fast_mode = kwargs.get("fast_mode") or True
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

        if kwargs.get("min_height") is not None:
            self.min_height = kwargs.get("min_height")
        else:
            try:
                self.min_height = self.get_block_height()
            except NetworkException:
                self.min_height = 0

    def get_balance(self):
        """
        Retrieves the balance of the Blockcypher Testnet address.

        Returns:
            float: The balance of the Blockcypher Testnet address in BCY.

        Raises:
            NetworkException: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo.amount
            if utxo.confirmed:
                confirmed_balance += utxo.amount
        return total_balance, confirmed_balance

    def get_utxos(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """

        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions) - 1, -1, -1):
            for out in self.transactions[i].outputs:
                if out.spent:
                    continue
                if out.address in self.addresses:
                    utxo = wallet_pb2.UTXO()
                    utxo.address = out.address
                    utxo.txid = self.transactions[i].txid
                    utxo.index = out.index
                    utxo.amount = out.amount
                    utxo.height = self.transactions[i].height
                    utxo.confirmed = self.transactions[i].confirmed
                    utxos.append(utxo)
        return utxos

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """

        url = "https://api.blockcypher.com/v1/bcy/test"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                params = None
                if self.api_key:
                    params = {"token", self.api_key}
                response = requests.get(url, params=params, timeout=60)
                break
            except requests.RequestException:
                pass
            except requests.exceptions.JSONDecodeError:
                pass

        if response.status_code == 200:
            data = response.json()
            self.height = data["height"]
            return self.height
        else:
            raise NetworkException("Failed to retrieve block height")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Blockcypher Testnet address from cached
        data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = deduplicate([*self._get_transaction_history()])
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0].txid
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs

        self.transactions = deduplicate(self.transactions)
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        params = None
        if self.api_key:
            params = {"token", self.api_key}
        for address in self.addresses:
            interval = 50
            block_height = 0

            # Set a very high UTXO limit for those rare address that have crazy high input/output counts.
            txlimit = 10000

            url = f"https://api.blockcypher.com/v1/bcy/test/addrs/{address}/full?limit={interval}&txlimit={txlimit}"
            for attempt in range(3, -1, -1):
                if attempt == 0:
                    raise NetworkException("Network request failure")
                try:
                    response = requests.get(url, params=params, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        break
                    else:
                        raise NetworkException("Failed to retrieve transaction history")
                except requests.RequestException:
                    pass

            for tx in data["txs"]:
                time.sleep(self.interval_sec / (self.requests * len(data["txs"])))
                if txhash and tx["hash"] == txhash:
                    return
                ctx = self._clean_tx(tx)
                if not ctx.confirmed or ctx.height >= self.min_height:
                    yield ctx
                else:
                    return
            if "hasMore" not in data.keys():
                return
            else:
                block_height = data["txs"][-1]["block_height"]

            while "hasMore" in data.keys() and data["hasMore"]:
                url = (
                    f"https://api.blockcypher.com/v1/bcy/test/addrs/{address}"
                    + f"/full?limit={interval}&before={block_height}&txlimit={txlimit}"
                )
                for attempt in range(3, -1, -1):
                    if attempt == 0:
                        raise NetworkException("Network request failure")
                    try:
                        response = requests.get(url, params=params, timeout=60)
                        break
                    except requests.RequestException:
                        pass

                if response.status_code == 200:
                    data = response.json()
                    for tx in data["txs"]:
                        time.sleep(
                            self.interval_sec / (self.requests * len(data["txs"]))
                        )
                        if txhash and tx["hash"] == txhash:
                            return
                        ctx = self._clean_tx(tx)
                        if not ctx.confirmed or ctx.height >= self.min_height:
                            yield ctx
                        else:
                            self.min_height = self.height + 1
                            return
                    if "hasMore" not in data.keys():
                        return
                    else:
                        block_height = data["txs"][-1]["block_height"]
                else:
                    raise NetworkException("Failed to retrieve transaction history")
