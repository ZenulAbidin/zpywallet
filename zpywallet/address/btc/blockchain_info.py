import requests
import time

from ...errors import NetworkException

class BlockchainInfoAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Blockchain.info API.

    The rate limits are 1 request per 10 seconds.

    THIS CLASS IS NOT RECOMMENDED for fetching transaction lists, because there's no way to get the transaction ID of inputs,
    and also because it does not return transaction vsize which is the measurement unit used by segwit blockchains.
    And speaking of blockchains, this backend only supports the Bitcoin mainnet.

    As a side effect of this, it is impossible to determine which transactions are RBFs and/or double-spends and exclude them
    accordingly. This means total balance may be incorrect. However, confirmed balance will still be correct in any case.

    Args:
        address (str): The human-readable Bitcoin address.

    Attributes:
        address (str): The human-readable Bitcoin address.
        transaction_history (list): The cached list of transactions.
        height (int): The last known block height.

    Methods:
        get_balance(): Retrieves the total and confirmed balances of the Bitcoin address.
        get_utxos(): Retrieves the UTXO set for this address
        get_block_height(): Retrieves the current block height.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """
    def __init__(self, address, request_interval=(1,10)):
        """
        Initializes an instance of the Address class.

        Args:
            address (str): The human-readable Bitcoin address.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.address = address
        self.requests, self.interval_sec = request_interval
        self.transactions = [*self._get_transaction_history()]
        self.height = self.get_block_height()

    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['hash']
        new_element['height'] = element['block_height']
        new_element['time'] = None

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            # Blockchain.info is crazy!
            # It has no input txid, only the address
            # So for now, we will substitute the address for the txid,
            # and once we get a sane API, we can fill in the txid properly.
            # (It also only supports Bitcoin, so there's that.)
            txinput['txid'] = ""
            txinput['index'] = vin['prev_out']['n']
            txinput['amount'] = vin['prev_out']['value'] / 1e8
            new_element['inputs'].append(txinput)
        
        for vout in element['out']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = vout['n']
            try:
                txoutput['address'] = vout['addr']
            except KeyError:
                txoutput['address'] = ''
            txoutput['spent'] = vout['spent']
            new_element['outputs'].append(txoutput)
        
        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = total_inputs - total_outputs

        # Blockchain.info API does not support vbytes. It only returns bytes.
        new_element['fee'] = new_element['total_fee'] / element['size']
        new_element['fee'] = 'byte'
        
        return new_element

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo["amount"]
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            if utxo["height"] is not None:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        self.height = self.get_block_height()
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for out in self.transactions[i]["outputs"]:
                if out["address"] == self.address and not out['spent']:
                    utxo = {}
                    utxo["address"] = self.address
                    utxo["txid"] = self.transactions[i]["txid"]
                    utxo["index"] = out["index"]
                    utxo["amount"] = out["amount"]
                    utxo["height"] = self.transactions[i]["height"]
                    utxos.append(utxo)
        
        # Now we will go through the UTXOs *again* to eliminate the RBF-replaced UTXOs.
        # The issue we are going to have is, *any* of the inputs could be the identical
        # one, because it only takes one input to RBF.

        # Unfortunately we CANNOT filter Blockchain.info UTXOs because they do not give us
        # the txids of inputs, and even the balance endpoint in the Blockchain Data API
        # returns the wrong total balance using exactly the same calculation.
        # Confirmed balances are not affected and still correct.
        return utxos

    def get_block_height(self):
        # Get the current block height now:
        url = "https://blockchain.info/latestblock"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                break
            except requests.RequestException:
                pass
        if response.status_code == 200:
            return response.json()["height"]
        else:
            raise NetworkException("Cannot get block height")


    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address from cached data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        self.height = self.get_block_height()
        if len(self.transactions) == 0:
            self.transactions = [*self.get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0]["txid"]
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
            del txs
        
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Bitcoin address. (internal method that makes the network query)

        Parameters:
            txhash (str): Get all transactions before (and not including) txhash.
                Defaults to None, which disables this behavior.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        interval = 50
        offset = 0

        url = f"https://blockchain.info/rawaddr/{self.address}?limit={interval}&offset={offset}"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                break
            except requests.RequestException:
                pass

        if response.status_code == 200:
            data = response.json()
            # The rate limit is 1 request every 10 seconds, so we will amortize the speed bump by sleeping every 200 milliseconds.
            # Since we have max 50 transactions, total execution time will be at least 10 seconds incuding the sleep time and user
            # code execution time, and if there are less than 50 transactions, we are finished fetching transactions anyway.
            for tx in data["txs"]:
                time.sleep(self.interval_sec/(self.requests*len(data["txs"])))
                if txhash and tx["hash"] == txhash:
                    return
                yield self._clean_tx(tx)
            n_tx = data["n_tx"]
            offset += min(interval, n_tx)
        else:
            raise NetworkException("Failed to retrieve transaction history")
        
        while offset < n_tx:
            # WARNING: RATE LIMIT IS 1 REQUEST PER 10 SECONDS.
            url = f"https://blockchain.info/rawaddr/{self.address}?limit={interval}&offset={offset}"
            for attempt in range(3, -1, -1):
                if attempt == 0:
                    raise NetworkException("Network request failure")
                try:
                    response = requests.get(url, timeout=60)
                    break
                except requests.RequestException:
                    pass

            if response.status_code == 200:
                data = response.json()
                for tx in data["txs"]:
                    time.sleep(self.interval_sec/(self.requests*len(data["txs"])))
                    if txhash and tx["hash"] == txhash:
                        return
                    yield self._clean_tx(tx)
                offset += interval
            else:
                raise NetworkException("Failed to retrieve transaction history")