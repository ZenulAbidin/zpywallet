#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

import random
import socket
import shutil
import time
import tempfile
import unittest
from pathlib import Path

import requests
from zpywallet.address import (
    CryptoClient,
    BlockcypherClient,
    BlockstreamClient,
    MempoolSpaceClient,
    SQLTransactionStorage,
    Web3Client,
)
from zpywallet.address.cache import DatabaseError
from zpywallet.address.fullnode import RPCClient
from zpywallet.errors import NetworkException
from .mock.btc import BitcoinMainUnit
from .mock.server import gen_random_port, spawn_server, exit_server

import multiprocessing

from zpywallet.generated import wallet_pb2
from zpywallet.generated.wallet_pb2 import Transaction, UTXO


def assemble_tx_proto(bin):
    result = []
    for b in bin:
        a = Transaction()
        a.ParseFromString(b)
        result.append(a)
    return result


def assemble_utxo_proto(bin):
    result = []
    for b in bin:
        a = UTXO()
        a.ParseFromString(b)
        result.append(a)
    return result


class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        pass

    def tearDown(self):
        """Tear down test fixtures."""
        pass

    def _sqlite_uri(self):
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, True)
        return f"sqlite:///{temp_dir / 'txcache.sqlite'}"

    def _wait_for_mock_server(self, server, port, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not server.is_alive():
                raise RuntimeError(f"Mock server exited before binding localhost:{port}")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                if sock.connect_ex(("localhost", port)) == 0:
                    return

            time.sleep(0.05)

        raise RuntimeError(f"Mock server did not bind localhost:{port} within {timeout}s")

    def _start_mock_server(self, responses, port):
        server = multiprocessing.Process(target=spawn_server, args=[responses, port])
        server.start()
        self._wait_for_mock_server(server, port)
        return server

    def test_000_btc_blockcypher_address(self):
        """Test fetching Bitcoin addresses with Blockcypher using mocked data."""
        port = gen_random_port()
        client = BlockcypherClient(
            [
                "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
            ],
            coin="BTC",
            chain="main",
            base_url=f"http://localhost:{port}",
        )
        try:
            server = self._start_mock_server(
                BitcoinMainUnit.BlockcypherTXHistoryResponseManager,
                port,
            )
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            with open('/tmp/outputproto', 'w') as f:
                f.write(str([t.SerializeToString() for t in tx_history]))
            self.assertEqual(
                tx_history,
                assemble_tx_proto(BitcoinMainUnit.BlockcypherExpectedTransactions),
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockcypherTXHistoryResponseManager,
                port,
            )
            client.base_url = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.BlockcypherExpectedUTXOs),
            )

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockcypherTXHistoryResponseManager,
                port,
            )
            client.base_url = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockcypherExpectedBalance)

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockcypherHeightResponseManager,
                port,
            )
            client.base_url = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.BlockcypherExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()

    def test_0001_btc_blockcypher_token_alias(self):
        """Test that the legacy token kwarg still populates the API key."""
        client = BlockcypherClient(
            ["3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V"],
            coin="BTC",
            chain="main",
            token="token-alias",
        )
        self.assertEqual(client.api_key, "token-alias")

    def test_0002_sql_transaction_storage_round_trip(self):
        """Test that sqlite-backed transaction storage can store and query txs."""
        storage = SQLTransactionStorage(self._sqlite_uri())
        storage.connect()

        transaction = Transaction()
        transaction.txid = "round-trip"
        transaction.timestamp = 123456789
        transaction.confirmed = True
        transaction.height = 42
        transaction.btclike_transaction.inputs.add(
            txid="prev", index=0, amount=2500, address="input-address"
        )
        transaction.btclike_transaction.outputs.add(
            index=0, amount=2000, address="output-address"
        )

        storage.store_transaction(transaction)
        storage.set_block_height(42)
        storage.commit()

        self.assertTrue(storage.have_transaction("round-trip"))
        self.assertEqual(storage.get_block_height(), 42)
        self.assertEqual(
            storage.get_transaction_by_txid("round-trip").txid, "round-trip"
        )
        self.assertEqual(
            [tx.txid for tx in storage.get_transactions_by_address("input-address")],
            ["round-trip"],
        )
        self.assertEqual(
            [tx.txid for tx in storage.get_transactions_by_address("output-address")],
            ["round-trip"],
        )

        storage.delete_transaction("round-trip")
        storage.commit()
        self.assertFalse(storage.have_transaction("round-trip"))

    def test_0002b_sql_transaction_storage_round_trip_canonical_eth_txid(self):
        """Test that canonical 0x-prefixed EVM txids round-trip through sqlite cache."""
        storage = SQLTransactionStorage(self._sqlite_uri())
        storage.connect()

        transaction = Transaction()
        transaction.txid = "0x" + ("ab" * 32)
        transaction.timestamp = 123456789
        transaction.confirmed = True
        transaction.height = 42
        transaction.fee_metric = wallet_pb2.FeeMetric.Value("WEI")
        transaction.ethlike_transaction.txfrom = (
            "0xd73e8e2ac0099169e7404f23c6caa94cf1884384"
        )
        transaction.ethlike_transaction.txto = (
            "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6"
        )
        transaction.ethlike_transaction.amount = 25
        transaction.ethlike_transaction.gas = 21000

        storage.store_transaction(transaction)
        storage.commit()

        self.assertTrue(storage.have_transaction(transaction.txid))
        self.assertEqual(
            storage.get_transaction_by_txid(transaction.txid).txid,
            transaction.txid,
        )
        self.assertEqual(
            [tx.txid for tx in storage.get_transactions_by_address(transaction.ethlike_transaction.txfrom)],
            [transaction.txid],
        )

    def test_0002c_sql_transaction_storage_widens_txid_columns_for_sql_backends(self):
        class RecordingStorage(SQLTransactionStorage):
            def __init__(self, protocol):
                self.connection_params = {"protocol": protocol}
                self.statements = []

            def _execute(self, sql, params=None):
                self.statements.append((sql, params or ()))

        postgres_storage = RecordingStorage("postgresql")
        postgres_storage._ensure_txid_column_capacity()
        self.assertEqual(
            [statement for statement, _params in postgres_storage.statements],
            [
                "ALTER TABLE transactions ALTER COLUMN txid TYPE VARCHAR(66)",
                "ALTER TABLE txos ALTER COLUMN txid TYPE VARCHAR(66)",
            ],
        )

        mysql_storage = RecordingStorage("mysql")
        mysql_storage._ensure_txid_column_capacity()
        self.assertEqual(
            [statement for statement, _params in mysql_storage.statements],
            [
                "ALTER TABLE transactions MODIFY COLUMN txid VARCHAR(66) NOT NULL",
                "ALTER TABLE txos MODIFY COLUMN txid VARCHAR(66) NOT NULL",
            ],
        )

    def test_0002d_sql_transaction_storage_connect_fails_closed_on_schema_error(self):
        class BrokenStorage(SQLTransactionStorage):
            def __init__(self, db_uri):
                super().__init__(db_uri)

            def create_transactions_table(self):
                raise DatabaseError("boom")

        storage = BrokenStorage(self._sqlite_uri())

        with self.assertRaisesRegex(DatabaseError, "boom"):
            storage.connect()

        self.assertIsNone(storage.container)

    def test_0003_rpc_client_reads_blocks_into_cache(self):
        """Test that the full-node reader syncs new blocks into sqlite cache."""

        class StubRPCClient(RPCClient):
            def __init__(self, db_uri):
                super().__init__(
                    ["cache-address"],
                    coin="BTC",
                    chain="main",
                    db_connection_parameters=db_uri,
                )
                self.mempool_read = False

            def _send_rpc_request(self, method, params=None):
                params = params or []
                if method == "getblockchaininfo":
                    return {"result": {"blocks": 2}}
                if method == "getblockhash":
                    return {"result": f"block-hash-{params[0]}"}
                if method == "getblock":
                    block_no = int(str(params[0]).rsplit("-", 1)[-1])
                    return {"result": {"tx": [f"tx-{block_no}"]}}
                raise AssertionError(f"Unexpected RPC method {method}")

            def _send_batch_rpc_request(self, reqs):
                for _method, params in reqs:
                    txid = params[0]
                    yield {"result": {"txid": txid, "vout": [], "vin": []}}

            def _clean_tx(self, element, block_height, _storage):
                transaction = Transaction()
                transaction.txid = element["txid"]
                transaction.confirmed = True
                transaction.height = block_height
                transaction.btclike_transaction.outputs.add(
                    index=0, amount=1, address="cache-address"
                )
                return transaction

            def read_mempool(self):
                self.mempool_read = True

        db_uri = self._sqlite_uri()
        client = StubRPCClient(db_uri)
        client.read_transaction_history()

        history = client.get_transaction_history()
        self.assertEqual([tx.txid for tx in history], ["tx-1", "tx-2"])
        self.assertTrue(client.mempool_read)

        storage = SQLTransactionStorage(db_uri)
        self.assertEqual(storage.get_block_height(), 2)

    def test_0004_rpc_client_parses_output_amounts_without_float_drift(self):
        client = RPCClient(["cache-address"], coin="BTC", chain="main")
        transaction = client._clean_tx(
            {
                "txid": "tx-float",
                "blocktime": 1,
                "vout": [
                    {
                        "value": 0.00000003,
                        "n": 0,
                        "scriptPubKey": {"address": "cache-address"},
                    }
                ],
                "vin": [{}],
                "size": 100,
            },
            1,
            None,
        )

        self.assertEqual(transaction.btclike_transaction.outputs[0].amount, 3)

    def test_0004a_rpc_client_uses_correct_dogecoin_testnet_port(self):
        client = RPCClient(["cache-address"], coin="DOGE", chain="test")

        self.assertEqual(client.rpc_port, 44555)
        self.assertEqual(client.rpc_url, "http://127.0.0.1:44555")

    def test_0004_web3_client_reads_blocks_into_cache(self):
        """Test that the web3 reader stores only matching txs in sqlite."""

        class FakeEth:
            block_number = 2

            def __init__(self):
                self.calls = []

            def get_block(self, block_number, full_transactions=True):
                self.calls.append((block_number, full_transactions))
                if block_number == "pending":
                    return {"transactions": []}
                return {
                    "timestamp": 123456 + block_number,
                    "transactions": [
                        {
                            "hash": bytes.fromhex(f"{block_number:064x}"),
                            "blockNumber": block_number,
                            "from": "0xd73e8e2ac0099169e7404f23c6caa94cf1884384",
                            "to": "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                            "value": 25,
                            "input": "0x1234",
                            "gas": 21000,
                            "gasPrice": 3,
                        },
                        {
                            "hash": bytes.fromhex(f"{block_number + 10:064x}"),
                            "blockNumber": block_number,
                            "from": "0x1111111111111111111111111111111111111111",
                            "to": "0x2222222222222222222222222222222222222222",
                            "value": 77,
                            "input": "0xabcd",
                            "gas": 25000,
                            "gasPrice": 5,
                        },
                    ],
                }

            def get_transaction_receipt(self, tx_hash):
                self.calls.append(("receipt", tx_hash))
                return {
                    "gasUsed": 15000,
                    "effectiveGasPrice": 4,
                }

        class FakeWeb3:
            def __init__(self):
                self.eth = FakeEth()

        db_uri = self._sqlite_uri()
        client = Web3Client(
            ["0xd73e8e2ac0099169e7404f23c6caa94cf1884384"],
            coin="ETH",
            chain="main",
            db_connection_parameters=db_uri,
            history_start_block=1,
            url="https://example.invalid",
        )
        client.web3 = FakeWeb3()
        client.read_mempool()

        history = client.get_transaction_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].ethlike_transaction.amount, 25)
        self.assertEqual(history[0].ethlike_transaction.gas, 15000)
        self.assertEqual(history[0].total_fee, 60000)
        self.assertEqual(history[0].ethlike_transaction.data, bytes.fromhex("1234"))
        self.assertEqual(
            len([call for call in client.web3.eth.calls if call[0] == "receipt"]), 2
        )
        self.assertNotIn(("pending", True), client.web3.eth.calls)

        storage = SQLTransactionStorage(db_uri)
        self.assertEqual(storage.get_block_height(), 2)

    def test_0004b_web3_client_requires_explicit_sync_bounds(self):
        class FakeEth:
            block_number = 2

            def set_gas_price_strategy(self, _strategy):
                return None

        class FakeMiddlewareOnion:
            def add(self, _middleware):
                return None

        class FakeWeb3:
            def __init__(self):
                self.eth = FakeEth()
                self.middleware_onion = FakeMiddlewareOnion()

        client = Web3Client(
            ["0xd73e8e2ac0099169e7404f23c6caa94cf1884384"],
            coin="ETH",
            chain="main",
            db_connection_parameters=self._sqlite_uri(),
            url="https://example.invalid",
        )
        client.web3 = FakeWeb3()

        with self.assertRaisesRegex(
            NetworkException, "history_start_block or history_lookback_blocks"
        ):
            client.read_mempool()

    def test_0005_crypto_client_initialize_database_fails_over_cache_providers(self):
        """Test that database initialization keeps trying cache providers after a failure."""

        class FailingProvider:
            def __init__(self):
                self.calls = 0

            def read_mempool(self):
                self.calls += 1
                raise NetworkException("first provider failed")

        class SucceedingProvider:
            def __init__(self):
                self.calls = 0

            def read_mempool(self):
                self.calls += 1

        client = CryptoClient.__new__(CryptoClient)
        first = FailingProvider()
        second = SucceedingProvider()
        client.cache_provider_list = [first, second]

        client.initialize_database()

        self.assertEqual(first.calls, 1)
        self.assertEqual(second.calls, 1)

    def test_0005b_crypto_client_raises_without_cached_history(self):
        class FailingProvider:
            def get_transaction_history(self):
                raise NetworkException("provider unavailable")

        client = CryptoClient.__new__(CryptoClient)
        client.coin = "BTC"
        client.cache_provider_list = []
        client.provider_list = [FailingProvider()]
        client.transactions = []

        with self.assertRaisesRegex(NetworkException, "provider unavailable"):
            client.get_transaction_history()

    def test_0005c_crypto_client_keeps_cached_history_on_provider_failure(self):
        class FailingProvider:
            def get_transaction_history(self):
                raise NetworkException("provider unavailable")

        cached_transaction = Transaction()
        cached_transaction.txid = "cached-tx"
        cached_transaction.height = 5

        client = CryptoClient.__new__(CryptoClient)
        client.coin = "BTC"
        client.cache_provider_list = []
        client.provider_list = [FailingProvider()]
        client.transactions = [cached_transaction]

        history = client.get_transaction_history()

        self.assertEqual([tx.txid for tx in history], ["cached-tx"])

    def test_0005d_crypto_client_eth_balance_raises_on_provider_failure(self):
        class FailingProvider:
            def get_balance(self):
                raise NetworkException("balance unavailable")

        client = CryptoClient.__new__(CryptoClient)
        client.coin = "ETH"
        client.cache_provider_list = [FailingProvider()]
        client.provider_list = []
        client.addresses = []
        client.transactions = []

        with self.assertRaisesRegex(NetworkException, "balance unavailable"):
            client.get_balance()

    def test_0005e_crypto_client_btc_balance_uses_cached_transactions(self):
        transaction = Transaction()
        transaction.txid = "cached-balance"
        transaction.confirmed = True
        transaction.height = 3
        transaction.btclike_transaction.outputs.add(
            index=0, amount=2500, address="cache-address", spent=False
        )

        client = CryptoClient.__new__(CryptoClient)
        client.coin = "BTC"
        client.cache_provider_list = []
        client.provider_list = []
        client.addresses = ["cache-address"]
        client.transactions = [transaction]

        self.assertEqual(client.get_balance(), (2500, 2500))

    def test_001_btc_blockstream_address(self):
        """Test fetching Bitcoin addresses with Blockstream using mocked data."""
        port = gen_random_port()
        try:
            server = self._start_mock_server(
                BitcoinMainUnit.BlockstreamTXHistoryResponseManager,
                port,
            )
            client = BlockstreamClient(
                [
                    "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                    "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
                ],
                coin="BTC",
                chain="main",
                base_url=f"http://localhost:{port}",
            )
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                tx_history,
                assemble_tx_proto(BitcoinMainUnit.BlockstreamExpectedTransactions),
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockstreamUTXOResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.BlockstreamExpectedUTXOs),
            )

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockstreamUTXOResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockstreamExpectedBalance)

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.BlockstreamHeightResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.BlockstreamExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()

    def test_002_btc_mempoolspace_address(self):
        """Test fetching Bitcoin addresses with MempoolSpace using mocked data."""
        port = gen_random_port()
        try:
            server = self._start_mock_server(
                BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager,
                port,
            )
            client = MempoolSpaceClient(
                [
                    "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                    "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
                ],
                coin="BTC",
                chain="main",
                base_url=f"http://localhost:{port}",
            )
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                tx_history,
                assemble_tx_proto(BitcoinMainUnit.MempoolSpaceExpectedTransactions),
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.MempoolSpaceUTXOResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.MempoolSpaceExpectedUTXOs),
            )

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.MempoolSpaceUTXOResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.MempoolSpaceExpectedBalance)

            port = gen_random_port()
            server = self._start_mock_server(
                BitcoinMainUnit.MempoolSpaceHeightResponseManager,
                port,
            )
            client.endpoint = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.MempoolSpaceExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()
