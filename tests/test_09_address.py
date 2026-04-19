#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

import random
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
)
from zpywallet.address.fullnode import RPCClient
from zpywallet.errors import NetworkException
from .mock.btc import BitcoinMainUnit
from .mock.server import gen_random_port, spawn_server, exit_server

import multiprocessing

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
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            # A race condition prevents us from immediately querying the local server.
            time.sleep(0.5)
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
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.base_url = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.BlockcypherExpectedUTXOs),
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.base_url = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockcypherExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherHeightResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
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

    def test_001_btc_blockstream_address(self):
        """Test fetching Bitcoin addresses with Blockstream using mocked data."""
        port = gen_random_port()
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
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
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.BlockstreamExpectedUTXOs),
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockstreamExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamHeightResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
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
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
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
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                utxos,
                assemble_utxo_proto(BitcoinMainUnit.MempoolSpaceExpectedUTXOs),
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.MempoolSpaceExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceHeightResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
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
