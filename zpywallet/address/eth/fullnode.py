from web3 import Web3, middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy

from ...errors import NetworkException
from ...generated import wallet_pb2
from ...utils.keccak import to_checksum_address


class EthereumWeb3Client:
    """Address querying class for Ethereum full nodes and Web3 clients.
    Most 3rd party providers e.g. Infura, QuickNode will also work here.

    WARNING: Ethereum nodes have a --txlookuplimit and maintain the last N transactions only,
    unless this option is turned off. 3rd party providers should have this switched off, but
    ensure it is turned off if you are running your own node.
    """

    def _clean_tx(self, element, block):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]
        if "blockNumber" in element.keys():
            new_element.confirmed = True
            new_element.height = element["blockNumber"]
        else:
            new_element.confirmed = False

        new_element.ethlike_transaction.txfrom = element["from"]
        new_element.ethlike_transaction.txto = element["to"]
        new_element.ethlike_transaction.amount = int(element["value"])

        new_element.timestamp = hex(block["timestamp"], 16)
        new_element.ethlike_transaction.data = element["input"]

        gas = int(element["gas"], 16)
        new_element.ethlike_transaction.gas = gas
        if "maxFeePerGas" in element.keys():
            new_element.total_fee = int(element["maxFeePerGas"], 16) * gas
        else:
            new_element.total_fee = int(element["gasPrice"]) * gas

        new_element.fee_metric = wallet_pb2.WEI
        return new_element

    def __init__(self, addresses, transactions=None, **kwargs):
        self.web3 = Web3(Web3.HTTPProvider(kwargs.get("url")))
        # This makes it fetch max<priority>feepergas info faster
        self.web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
        self.web3.middleware_onion.add(middleware.time_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.simple_cache_middleware)

        self.min_height = kwargs.get("min_height") or 0
        self.fast_mode = kwargs.get("fast_mode") or True
        self.transactions = []
        self.addresses = [to_checksum_address(a) for a in addresses]
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

        if kwargs.get("min_height") is not None:
            self.min_height = kwargs.get("min_height")
        else:
            try:
                self.min_height = self.get_block_height() + 1
            except NetworkException:
                self.min_height = 0

    def get_transaction_history(self):
        self.transactions = [*self._get_transaction_history()]
        return self.transactions

    def get_block_height(self):
        try:
            return self.web3.eth.block_number
        except Exception as e:
            raise NetworkException("Failed to invoke Web3 method")

    def get_balance(self):
        """
        Retrieves the balance of the Ethereum address.

        The ETH balance can be obtained without fetching the Ethereum transactions first.

        Returns:
            int: The balance of the Ethereum address in Gwei.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        balance = 0
        for address in self.addresses:
            try:
                balance += self.web3.eth.get_balance(address)
            except Exception as e:
                raise NetworkException("Failed to invoke Web3 method")

        # Ethereum has no unconfirmed balances or transactions.
        # But for compatibility reasons, we still return it as a 2-tuple.
        return (balance, balance)

    # In Ethereum, only one transaction per account can be included in a block at a time.
    def _get_transaction_history(self):

        addresses = [a.lower() for a in self.addresses]

        for block_number in range(self.block_height, self.get_block_height() + 1):
            # Retrieve block information
            try:
                block = self.web3.eth.getBlock(block_number, full_transactions=True)
            except Exception as e:
                raise NetworkException("Failed to invoke Web3 method")

            # Check if the block contains transactions
            if block and "transactions" in block:
                transactions = block["transactions"]

                # Iterate through transactions in the block
                for tx_hash in transactions:
                    # Retrieve transaction details
                    transaction = self.web3.eth.getTransaction(tx_hash)

                    # Check if the transaction is related to the target address
                    if transaction and transaction["to"].lower() in addresses:
                        yield self._clean_tx(transaction, block)
