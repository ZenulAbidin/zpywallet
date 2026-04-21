from .blockcypher import BlockcypherClient
from .blockstream import BlockstreamClient
from .esplora import EsploraClient
from .fullnode import RPCClient
from .mempoolspace import MempoolSpaceClient
from .web3node import Web3Client
from ..generated import wallet_pb2
from ..errors import NetworkException
from .provider import AddressProvider
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory

# TODO we currently have no easy way to update cache providers asynchronously.


class CryptoClient(AddressProvider):
    """Represents a list of crypto addresses.

    Developers should use this class, because it autoselects the most stable
    providers to fetch data from.
    """

    def __init__(
        self,
        addresses,
        coin="BTC",
        chain="main",
        use_database=False,
        transactions=None,
        **kwargs,
    ):
        super().__init__(addresses, transactions=transactions)
        self.coin = coin.upper()
        self.cache_provider_list = []
        self.provider_list = []
        self.current_index = 0
        self._database_initialized = False
        fullnode_endpoints = kwargs.get("fullnode_endpoints") or []
        esplora_endpoints = kwargs.get("esplora_endpoints") or []
        blockcypher_tokens = kwargs.get("blockcypher_tokens") or []
        history_start_block = kwargs.get("history_start_block")
        history_lookback_blocks = kwargs.get("history_lookback_blocks")
        allow_unbounded_history_sync = kwargs.get(
            "allow_unbounded_history_sync", False
        )
        include_pending_history = kwargs.get("include_pending_history", False)
        self._db_tempdir = None
        self.db_connection_parameters = None
        if use_database:
            self.db_connection_parameters = kwargs.get("db_connection_parameters")
            if not self.db_connection_parameters:
                # The docs promise sqlite as the default DBAPI backend.
                self._db_tempdir = TemporaryDirectory(prefix="zpywallet-")
                db_path = Path(self._db_tempdir.name) / "txcache.sqlite"
                self.db_connection_parameters = f"sqlite:///{db_path}"

        if use_database:
            for endpoint in fullnode_endpoints:
                with suppress(ValueError, NetworkException):
                    self.cache_provider_list.append(
                        RPCClient(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            history_start_block=history_start_block,
                            history_lookback_blocks=history_lookback_blocks,
                            allow_unbounded_history_sync=allow_unbounded_history_sync,
                            include_pending_history=include_pending_history,
                            **endpoint,
                        )
                    )

                with suppress(ValueError, NetworkException):
                    self.cache_provider_list.append(
                        Web3Client(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            history_start_block=history_start_block,
                            history_lookback_blocks=history_lookback_blocks,
                            allow_unbounded_history_sync=allow_unbounded_history_sync,
                            include_pending_history=include_pending_history,
                            **endpoint,
                        )
                    )

            for endpoint in esplora_endpoints:
                with suppress(ValueError, NetworkException):
                    self.cache_provider_list.append(
                        EsploraClient(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            history_start_block=history_start_block,
                            **endpoint,
                        )
                    )

            with suppress(ValueError, NetworkException):
                self.cache_provider_list.append(
                    BlockstreamClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        db_connection_parameters=self.db_connection_parameters,
                        history_start_block=history_start_block,
                    )
                )

            with suppress(ValueError, NetworkException):
                self.cache_provider_list.append(
                    MempoolSpaceClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        db_connection_parameters=self.db_connection_parameters,
                        history_start_block=history_start_block,
                    )
                )

        for token in blockcypher_tokens:
            with suppress(ValueError, NetworkException):
                self.provider_list.append(
                    BlockcypherClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        token=token,
                    )
                )

        # Blockcypher without any token
        with suppress(ValueError, NetworkException):
            self.provider_list.append(
                BlockcypherClient(
                    addresses,
                    coin,
                    chain,
                    transactions=self.transactions,
                )
            )

        if not self.provider_list and not self.cache_provider_list:
            raise ValueError(f"No providers for coin '{coin}', chain '{chain}' found.")

    def _advance_to_next_provider(self):
        if not self.provider_list:
            return

        newindex = (self.current_index + 1) % len(self.provider_list)
        self.provider_list[newindex].transactions = self.provider_list[
            self.current_index
        ].transactions
        self.current_index = newindex

    def initialize_database(self):
        last_error = None
        for provider in self.cache_provider_list:
            # They all use the same database so we can just read the mempool
            # from the first one to populate the database.
            try:
                provider.read_mempool()
                self._database_initialized = True
                return
            except NetworkException as e:
                last_error = e
                continue

        if last_error is not None:
            raise last_error

        raise NetworkException("Failed to populate database - no cache providers available")

    def get_balance(self):
        last_error = None
        for provider in self.cache_provider_list:
            try:
                return provider.get_balance()
            except NetworkException as e:
                last_error = e
                continue

        for provider in self.provider_list:
            try:
                return provider.get_balance()
            except NetworkException as e:
                last_error = e
                continue

        if self.coin == "ETH":
            if last_error is not None:
                raise last_error
            raise NetworkException("All address providers failed to get balance")

        return super().get_balance()

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """
        for provider in self.cache_provider_list:
            try:
                h = provider.get_block_height()
                if h > 0:
                    return h
            except NetworkException:
                continue

        for provider in self.provider_list:
            try:
                h = provider.get_block_height()
                if h > 0:
                    return h
            except NetworkException:
                continue

        raise NetworkException("All address providers failed to get block height")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Litecoin address from cached
        data augmented with network data.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """
        min_height = (
            0
            if not self.transactions
            else max([tx.height for tx in self.transactions] + [-1])
        )

        last_error = None
        provider_succeeded = False
        for provider in self.cache_provider_list + self.provider_list:
            provider.transactions = self.transactions
            provider.height = min_height
            try:
                provider.get_transaction_history()
                self.transactions = provider.transactions
                provider_succeeded = True
                break
            except NetworkException as e:
                last_error = e
                continue

        if not provider_succeeded and not self.transactions and last_error is not None:
            raise last_error

        return self.transactions
