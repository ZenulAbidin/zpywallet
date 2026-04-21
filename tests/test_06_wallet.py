#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for using the Wallet class."""


import unittest
import asyncio
import os
import time
from types import SimpleNamespace
from unittest.mock import patch
from zpywallet.generated import wallet_pb2
from zpywallet import Wallet
from zpywallet.address.cache import SQLTransactionStorage
from zpywallet.destination import Destination, FeePolicy
from zpywallet.broadcast.btc import all as btc_broadcast_all
from zpywallet.errors import NetworkException
from zpywallet.network import (
    BitcoinSegwitMainNet,
    EthereumMainNet,
    EthereumSepoliaTestNet,
)
from zpywallet.nodes.ethsepolia import ethsepolia_nodes
from zpywallet.transaction import Transaction
from zpywallet.utxo import UTXO

RUN_LIVE_TESTS = os.getenv("ZPYWALLET_RUN_LIVE_TESTS") == "1"


class TestWallet(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_create_wallet(self):
        _ = Wallet(BitcoinSegwitMainNet, None, "zpywallet", receive_gap_limit=1)
        wallet_1 = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        exported_wallet = wallet_1.serialize()
        restored_wallet = Wallet.deserialize(exported_wallet, "zpywallet")
        self.assertIsNotNone(restored_wallet)
        self.assertEqual(restored_wallet.addresses(), wallet_1.addresses())

    def test_001_wallet_transaction_history(self):
        """Test using the wallet."""
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        # wallet.get_transaction_history()
        # wallet.get_utxos(only_unspent=False)
        # wallet.get_utxos(only_unspent=True)
        # wallet.get_balance()

    def test_002_wallet_helpers(self):
        """Test using the wallet."""
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        wallet.addresses()
        wallet.random_address()
        wallet.private_keys("zpywallet")
        # This seems to work off and on inside Pytest/TOX
        with self.assertRaises(ValueError):
            wallet.private_keys("wrongpassword")

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_003_wallet_broadcast(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        wallet._add_stock_nodes()
        wallet.broadcast_transaction(
            b"010000000113f3b5446192eeb85c0f7ca64c12196c26314d27b5ab6a976d560cb134ffa82f020000006b483045022100deb556a5c301696f5def1888e54e8c1227caeb3ed4ae7b1c665af79174f50ab702201a59bba811554bd66fa003606ba852bf17699f38c6b1c3f8628f36c9d193a081012102245a4ecd8ad47f171f90c6d4a4f929052814d844e4d8c112bbf799aedc1b8555ffffffff061953cb010000000017a9145bf7f29863984cd9c8ff321a6d93d6344c7c055287102cf604000000001976a9148e09dee91c997fd306030ad7a1c46f17dcd51fdd88ace00f97000000000017a914ecd0679169813020faa97b418be8e79098c1cd55871595c1000000000017a914b61a3c9897d3d539aee6ad7327dfbd2192103e6287a4b62100000000001976a9144954c267b47bd1f864e627ca5b9c82b1fde8966188ac9e41a409000000001976a9141199950f4896dbbbd5ddc833092f5458b5f3154888ac00000000"
        )

    def test_003b_wallet_broadcast_returns_provider_results(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )

        with patch(
            "zpywallet.wallet.broadcast_transaction", return_value=["ok"]
        ) as broadcast:
            result = wallet.broadcast_transaction("deadbeef")

        self.assertEqual(result, ["ok"])
        broadcast.assert_called_once_with("deadbeef", BitcoinSegwitMainNet)

    def test_004_wallet_utxos(self):
        """Test using the wallet."""
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        saved_utxos = [
            b'\x08\xc0\x84=\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@dce83bbde7aba21c8994f9176e827a6a6ce28b4e4121d9090d8fe0b846b74034 \x010\x018\xc6\x82\t',
            b'\x08\xa8U\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@2de38a49f0079d0aaa8a0b9cfec71b1af935752b609eee0dc1eae56b2162a7e2 \x010\x018\x88\xef\x11',
            b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x040\x018\x91\xf2\x1e',
            b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x050\x018\x91\xf2\x1e',
            b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x060\x018\x91\xf2\x1e',
            b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x080\x018\x91\xf2\x1e',
            b'\x08\x9e\x9b\x01\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@83d0aaf8e3bd5a240eba1061c572024750c38c847074f7717ef8467b3c4e38930\x018\xe0\xc5!',
            b'\x08\xa4!\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@ca9ae53f5a8bf29825af1438fcde86c4437668f5ed35ec32b9fc4e5a0a42da680\x018\xe1\xc5!',
        ]
        utxos = []
        for u in saved_utxos:
            utxo = wallet_pb2.UTXO()
            utxo.ParseFromString(u)
            utxos.append(utxo)

        wallet._to_human_friendly_utxo(utxos, [])

    def test_005_eth_wallet_create_transaction(self):
        wallet = Wallet(
            EthereumMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )

        destinations = [
            Destination(
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                0.00000002,
                EthereumMainNet,
            )
        ]

        with patch("zpywallet.wallet.create_transaction", return_value=b"signed") as tx:
            signed = wallet.create_transaction(
                "zpywallet",
                destinations,
                gas=21000,
                nonce=9,
                data="0x1234",
                max_fee_per_gas=30,
                max_priority_fee_per_gas=2,
            )

        self.assertEqual(signed, b"signed")
        args, kwargs = tx.call_args
        self.assertEqual(args[0][0].address(), wallet.addresses()[0])
        self.assertEqual(args[1], destinations)
        self.assertEqual(kwargs["network"], EthereumMainNet)
        self.assertIn("full_nodes", kwargs)
        self.assertEqual(kwargs["nonce"], 9)
        self.assertEqual(kwargs["data"], "0x1234")
        self.assertEqual(kwargs["max_fee_per_gas"], 30)
        self.assertEqual(kwargs["max_priority_fee_per_gas"], 2)

    def test_006_eth_wallet_history_uses_default_sqlite_cache(self):
        wallet = Wallet(
            EthereumMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        db_uri = wallet.client.db_connection_parameters

        self.assertTrue(db_uri.startswith("sqlite:///"))
        self.assertTrue(wallet.client.cache_provider_list)
        self.assertTrue(
            all(
                provider.db_connection_parameters == db_uri
                for provider in wallet.client.cache_provider_list
            )
        )
        cached_address = wallet.client.cache_provider_list[0].addresses[0]

        transaction = wallet_pb2.Transaction(
            txid="eth-tx-1",
            timestamp=1234567890,
            confirmed=True,
            height=1,
            total_fee=42000,
            fee_metric=wallet_pb2.FeeMetric.Value("WEI"),
        )
        transaction.ethlike_transaction.txfrom = cached_address
        transaction.ethlike_transaction.txto = (
            "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6"
        )
        transaction.ethlike_transaction.amount = 25
        transaction.ethlike_transaction.gas = 21000

        storage = SQLTransactionStorage(db_uri)
        storage.store_transaction(transaction)
        storage.commit()

        history = wallet.get_transaction_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].txid(), "eth-tx-1")
        self.assertEqual(history[0].evm_from(), cached_address)
        self.assertEqual(history[0].evm_gas(), 21000)

    def test_006_wallet_create_transaction_executes_btc_flow(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        fake_utxo = UTXO(
            None,
            None,
            _network=BitcoinSegwitMainNet,
            _internal_param_do_not_use={
                "txid": "00" * 32,
                "index": 0,
                "amount": 50000,
                "address": source_address,
                "height": 1,
            },
        )
        destinations = [Destination(source_address, 0.0001, BitcoinSegwitMainNet)]

        with patch.object(wallet, "get_utxos", return_value=[fake_utxo]):
            signed = wallet.create_transaction("zpywallet", destinations, fee_rate=1)

        self.assertIsInstance(signed, str)
        self.assertRegex(signed, r"^[0-9a-f]+$")

    def test_007_wallet_get_balance_counts_only_confirmed_utxos(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        confirmed = SimpleNamespace(
            amount=lambda in_standard_units=True: 0.001 if in_standard_units else 100000,
            height=lambda: 42,
        )
        unconfirmed = SimpleNamespace(
            amount=lambda in_standard_units=True: 0.002 if in_standard_units else 200000,
            height=lambda: 0,
        )

        with patch.object(wallet, "get_utxos", return_value=[confirmed, unconfirmed]):
            total_balance, confirmed_balance = wallet.get_balance()

        self.assertEqual(total_balance, 0.003)
        self.assertEqual(confirmed_balance, 0.001)

    def test_008_random_address_uses_enough_entropy_bytes(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1000,
        )
        reader = SimpleNamespace(calls=[])

        def read(byte_count):
            reader.calls.append(byte_count)
            return b"\x03\xe7"[:byte_count]

        reader.read = read

        with patch("zpywallet.wallet.Random.new", return_value=reader):
            address = wallet.random_address()

        self.assertEqual(reader.calls, [2])
        self.assertEqual(address, wallet.addresses()[999])

    def test_008b_wallet_defaults_change_gap_limit_to_receive_gap_limit(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=2,
        )

        self.assertEqual(wallet.container.change_gap_limit, 2)
        self.assertEqual(len(wallet._change_addresses), 2)

    def test_009_wallet_tracks_change_branch_separately(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            change_gap_limit=1,
        )
        change_address = wallet.client.addresses[1]
        fake_utxo = UTXO(
            None,
            None,
            _network=BitcoinSegwitMainNet,
            _internal_param_do_not_use={
                "txid": "11" * 32,
                "index": 0,
                "amount": 1000,
                "address": change_address,
                "height": 1,
            },
        )

        self.assertEqual(len(wallet.addresses()), 1)
        self.assertEqual(len(wallet.client.addresses), 2)
        self.assertNotIn(change_address, wallet.addresses())

        matched = wallet._to_human_friendly_utxo(
            [fake_utxo], wallet._spend_private_keys("zpywallet")
        )

        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]._output["address"], change_address)

    def test_010_wallet_calculate_change_uses_internal_branch(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            change_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        change_address = wallet.client.addresses[1]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 50000),
        ]
        destinations = [Destination(source_address, 0.0001, BitcoinSegwitMainNet)]

        with patch(
            "zpywallet.wallet.create_transaction",
            side_effect=lambda _inputs, outputs, **kwargs: f"len-{len(outputs)}",
        ):
            with patch(
                "zpywallet.wallet.transaction_size_simple",
                side_effect=lambda raw: {"len-1": 90, "len-2": 100}[raw],
            ):
                adjusted_destinations, change = wallet._calculate_change(
                    inputs, destinations, fee_rate=1
                )

        self.assertEqual(
            [d.amount(in_standard_units=False) for d in adjusted_destinations], [10000]
        )
        self.assertEqual(change.address(), change_address)
        self.assertNotIn(change.address(), wallet.addresses())

    def test_011_wallet_change_uses_raw_unit_arithmetic(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            change_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 50000),
        ]
        destinations = [
            Destination(
                source_address,
                49950,
                BitcoinSegwitMainNet,
                fee_policy=FeePolicy.PROPORTIONAL,
                in_standard_units=False,
            )
        ]

        with patch(
            "zpywallet.wallet.create_transaction",
            side_effect=lambda _inputs, outputs, **kwargs: f"len-{len(outputs)}",
        ):
            with patch(
                "zpywallet.wallet.transaction_size_simple",
                side_effect=lambda raw: {"len-1": 100, "len-2": 134}[raw],
            ):
                adjusted_destinations, change = wallet._calculate_change(
                    inputs, destinations, fee_rate=1
                )

        self.assertIsNone(change)
        self.assertEqual(
            [d.amount(in_standard_units=False) for d in adjusted_destinations], [49900]
        )

    def test_012_wallet_get_utxos_can_include_spent_outputs(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        address = wallet.addresses()[0]

        tx = wallet_pb2.Transaction(
            txid="tx1",
            timestamp=1,
            confirmed=True,
            height=1,
            fee_metric=wallet_pb2.FeeMetric.Value("BYTE"),
        )
        spent_output = tx.btclike_transaction.outputs.add()
        spent_output.address = address
        spent_output.index = 0
        spent_output.amount = 100
        spent_output.spent = True

        unspent_output = tx.btclike_transaction.outputs.add()
        unspent_output.address = address
        unspent_output.index = 1
        unspent_output.amount = 200
        unspent_output.spent = False

        with patch.object(
            wallet,
            "get_transaction_history",
            return_value=[Transaction(tx, BitcoinSegwitMainNet)],
        ):
            utxos = wallet.get_utxos(only_unspent=False)

        self.assertEqual(
            [(u.index(), u.amount(False), u.spent()) for u in utxos],
            [(0, 100, True), (1, 200, False)],
        )

    def test_006_wallet_broadcast_runs_providers_concurrently(self):
        async def blocking_provider(*args, **kwargs):
            time.sleep(0.1)

        with patch.multiple(
            btc_broadcast_all,
            broadcast_transaction_btc_bitaps=blocking_provider,
            broadcast_transaction_btc_blockchain_info=blocking_provider,
            broadcast_transaction_btc_blockchair=blocking_provider,
            broadcast_transaction_btc_blockcypher=blocking_provider,
            broadcast_transaction_btc_blockstream=blocking_provider,
            broadcast_transaction_btc_mempool_space=blocking_provider,
            broadcast_transaction_btc_smartbit=blocking_provider,
            broadcast_transaction_btc_viabtc=blocking_provider,
            btc_nodes=[],
            btc_esplora_nodes=[],
        ):
            start = time.monotonic()
            asyncio.run(
                btc_broadcast_all.broadcast_transaction_btc(
                    "00", rpc_nodes=[], esplora_nodes=[]
                )
            )
            elapsed = time.monotonic() - start

        self.assertLess(elapsed, 0.4)

    def test_013_wallet_create_transaction_applies_proportional_fee_outputs(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        destinations = [
            Destination(
                source_address,
                950,
                BitcoinSegwitMainNet,
                fee_policy=FeePolicy.PROPORTIONAL,
                in_standard_units=False,
            )
        ]
        fake_utxo = UTXO(
            None,
            None,
            _network=BitcoinSegwitMainNet,
            _internal_param_do_not_use={
                "txid": "22" * 32,
                "index": 0,
                "amount": 1000,
                "address": source_address,
                "height": 1,
            },
        )
        captured_outputs = []

        def fake_create_transaction(_inputs, outputs, **kwargs):
            captured_outputs.append(
                [o.amount(in_standard_units=False) for o in outputs]
            )
            return f"len-{len(outputs)}"

        with patch.object(wallet, "get_utxos", return_value=[fake_utxo]):
            with patch(
                "zpywallet.wallet.create_transaction",
                side_effect=fake_create_transaction,
            ):
                with patch(
                    "zpywallet.wallet.transaction_size_simple",
                    side_effect=lambda raw: {"len-1": 100, "len-2": 120}[raw],
                ):
                    signed = wallet.create_transaction(
                        "zpywallet", destinations, fee_rate=1
                    )

        self.assertEqual(signed, "len-1")
        self.assertEqual(captured_outputs[-1], [900])
        self.assertEqual(destinations[0].amount(in_standard_units=False), 950)

    def test_014_wallet_create_transaction_allows_exact_spend_without_change(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        destinations = [
            Destination(
                source_address,
                900,
                BitcoinSegwitMainNet,
                in_standard_units=False,
            )
        ]
        fake_utxo = UTXO(
            None,
            None,
            _network=BitcoinSegwitMainNet,
            _internal_param_do_not_use={
                "txid": "33" * 32,
                "index": 0,
                "amount": 1000,
                "address": source_address,
                "height": 1,
            },
        )
        captured_outputs = []

        def fake_create_transaction(_inputs, outputs, **kwargs):
            captured_outputs.append(
                [o.amount(in_standard_units=False) for o in outputs]
            )
            return f"len-{len(outputs)}"

        with patch.object(wallet, "get_utxos", return_value=[fake_utxo]):
            with patch(
                "zpywallet.wallet.create_transaction",
                side_effect=fake_create_transaction,
            ):
                with patch(
                    "zpywallet.wallet.transaction_size_simple",
                    side_effect=lambda raw: {"len-1": 100, "len-2": 120}[raw],
                ):
                    signed = wallet.create_transaction(
                        "zpywallet", destinations, fee_rate=1
                    )

        self.assertEqual(signed, "len-1")
        self.assertEqual(captured_outputs[-1], [900])
        self.assertEqual(len(destinations), 1)
        self.assertEqual(destinations[0].amount(in_standard_units=False), 900)

    def test_015_eth_wallet_history_bootstraps_cache_on_first_request(self):
        wallet = Wallet(
            EthereumMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            history_start_block=1,
        )
        transaction = wallet_pb2.Transaction(
            txid="eth-bootstrap-1",
            timestamp=1234567890,
            confirmed=True,
            height=1,
            total_fee=21000,
            fee_metric=wallet_pb2.FeeMetric.Value("WEI"),
        )
        transaction.ethlike_transaction.txfrom = wallet.addresses()[0]

        with patch.object(
            wallet.client,
            "get_transaction_history",
            side_effect=[[], [transaction]],
        ) as get_history, patch.object(wallet.client, "initialize_database") as init_db:
            history = wallet.get_transaction_history()

        init_db.assert_called_once()
        self.assertEqual(get_history.call_count, 2)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].txid(), "eth-bootstrap-1")

    def test_015a_eth_wallet_history_deduplicates_mixed_txid_forms(self):
        wallet = Wallet(
            EthereumMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        bare_txid = "ab" * 32
        transaction_1 = wallet_pb2.Transaction(
            txid=bare_txid,
            timestamp=1234567890,
            confirmed=True,
            height=1,
            total_fee=21000,
            fee_metric=wallet_pb2.FeeMetric.Value("WEI"),
        )
        transaction_1.ethlike_transaction.txfrom = wallet.addresses()[0]

        transaction_2 = wallet_pb2.Transaction(
            txid="0x" + bare_txid.upper(),
            timestamp=1234567891,
            confirmed=True,
            height=2,
            total_fee=22000,
            fee_metric=wallet_pb2.FeeMetric.Value("WEI"),
        )
        transaction_2.ethlike_transaction.txfrom = wallet.addresses()[0]

        with patch.object(
            wallet.client,
            "get_transaction_history",
            return_value=[transaction_1, transaction_2],
        ):
            history = wallet.get_transaction_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].txid(), "0x" + bare_txid)

    def test_015b_eth_wallet_history_requires_explicit_sync_bounds(self):
        wallet = Wallet(
            EthereumMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )

        with patch.object(
            wallet.client,
            "get_transaction_history",
            return_value=[],
        ), patch.object(
            wallet.client,
            "initialize_database",
            side_effect=NetworkException(
                "EVM history sync requires history_start_block or "
                "history_lookback_blocks; unbounded sync is disabled by default"
            ),
        ):
            with self.assertRaisesRegex(
                NetworkException, "history_start_block or history_lookback_blocks"
            ):
                wallet.get_transaction_history()

    def test_016_eth_sepolia_wallet_round_trips(self):
        wallet = Wallet(
            EthereumSepoliaTestNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )

        restored_wallet = Wallet.deserialize(wallet.serialize(), "zpywallet")

        self.assertIs(restored_wallet.network(), EthereumSepoliaTestNet)
        self.assertEqual(restored_wallet.addresses(), wallet.addresses())
        self.assertEqual(wallet._add_stock_nodes()[0]["url"], ethsepolia_nodes[0]["url"])

    def test_017_wallet_select_inputs_uses_smallest_sufficient_single_utxo(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        destinations = [Destination(wallet.addresses()[0], 1000, BitcoinSegwitMainNet)]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 900, height=lambda: 1),
            SimpleNamespace(amount=lambda in_standard_units=False: 2000, height=lambda: 2),
            SimpleNamespace(amount=lambda in_standard_units=False: 5000, height=lambda: 3),
        ]

        def fake_calculate_change(selected_inputs, _destinations, _fee_rate):
            total = sum(i.amount(in_standard_units=False) for i in selected_inputs)
            if total < 1500:
                raise ValueError("insufficient")
            return _destinations, None

        with patch.object(wallet, "_calculate_change", side_effect=fake_calculate_change):
            selected_inputs = wallet._select_inputs(inputs, destinations, fee_rate=1)

        self.assertEqual(
            [i.amount(in_standard_units=False) for i in selected_inputs],
            [2000],
        )

    def test_018_wallet_select_inputs_accumulates_largest_first_when_needed(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        destinations = [Destination(wallet.addresses()[0], 1000, BitcoinSegwitMainNet)]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 4000, height=lambda: 1),
            SimpleNamespace(amount=lambda in_standard_units=False: 3500, height=lambda: 2),
            SimpleNamespace(amount=lambda in_standard_units=False: 2000, height=lambda: 3),
        ]

        def fake_calculate_change(selected_inputs, _destinations, _fee_rate):
            total = sum(i.amount(in_standard_units=False) for i in selected_inputs)
            if total < 7000:
                raise ValueError("insufficient")
            return _destinations, None

        with patch.object(wallet, "_calculate_change", side_effect=fake_calculate_change):
            selected_inputs = wallet._select_inputs(inputs, destinations, fee_rate=1)

        self.assertEqual(
            [i.amount(in_standard_units=False) for i in selected_inputs],
            [4000, 3500],
        )

    def test_019_wallet_calculate_change_drops_uneconomic_change(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            change_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 10150),
        ]
        destinations = [
            Destination(
                source_address,
                10000,
                BitcoinSegwitMainNet,
                in_standard_units=False,
            )
        ]

        with patch(
            "zpywallet.wallet.create_transaction",
            side_effect=lambda _inputs, outputs, **kwargs: f"len-{len(outputs)}",
        ):
            with patch(
                "zpywallet.wallet.transaction_size_simple",
                side_effect=lambda raw: {"len-1": 90, "len-2": 100}[raw],
            ):
                adjusted_destinations, change = wallet._calculate_change(
                    inputs, destinations, fee_rate=1
                )

        self.assertEqual(
            [d.amount(in_standard_units=False) for d in adjusted_destinations], [10000]
        )
        self.assertIsNone(change)

    def test_020_wallet_fractional_fee_rates_round_up_to_raw_units(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        destinations = [
            Destination(
                source_address,
                940,
                BitcoinSegwitMainNet,
                fee_policy=FeePolicy.PROPORTIONAL,
                in_standard_units=False,
            )
        ]
        fake_utxo = UTXO(
            None,
            None,
            _network=BitcoinSegwitMainNet,
            _internal_param_do_not_use={
                "txid": "44" * 32,
                "index": 0,
                "amount": 999,
                "address": source_address,
                "height": 1,
            },
        )
        captured_outputs = []

        def fake_create_transaction(_inputs, outputs, **kwargs):
            captured_outputs.append(
                [o.amount(in_standard_units=False) for o in outputs]
            )
            return f"len-{len(outputs)}"

        with patch.object(wallet, "get_utxos", return_value=[fake_utxo]):
            with patch(
                "zpywallet.wallet.create_transaction",
                side_effect=fake_create_transaction,
            ):
                with patch(
                    "zpywallet.wallet.transaction_size_simple",
                    side_effect=lambda raw: {"len-1": 100, "len-2": 120}[raw],
                ):
                    signed = wallet.create_transaction(
                        "zpywallet", destinations, fee_rate=0.595
                    )

        self.assertEqual(signed, "len-1")
        self.assertEqual(captured_outputs[-1], [939])
        self.assertEqual(destinations[0].amount(in_standard_units=False), 940)

    def test_021_wallet_create_transaction_rejects_dust_destination(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
        )
        destinations = [
            Destination(
                wallet.addresses()[0],
                545,
                BitcoinSegwitMainNet,
                in_standard_units=False,
            )
        ]

        with self.assertRaisesRegex(ValueError, "dust threshold"):
            wallet.create_transaction("zpywallet", destinations, fee_rate=1)

    def test_022_wallet_proportional_fee_rejects_dust_output(self):
        wallet = Wallet(
            BitcoinSegwitMainNet,
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
            "zpywallet",
            receive_gap_limit=1,
            change_gap_limit=1,
        )
        source_address = wallet.addresses()[0]
        inputs = [
            SimpleNamespace(amount=lambda in_standard_units=False: 645),
        ]
        destinations = [
            Destination(
                source_address,
                600,
                BitcoinSegwitMainNet,
                fee_policy=FeePolicy.PROPORTIONAL,
                in_standard_units=False,
            )
        ]

        with patch(
            "zpywallet.wallet.create_transaction",
            side_effect=lambda _inputs, outputs, **kwargs: f"len-{len(outputs)}",
        ):
            with patch(
                "zpywallet.wallet.transaction_size_simple",
                side_effect=lambda raw: {"len-1": 100, "len-2": 120}[raw],
            ):
                with self.assertRaisesRegex(ValueError, "dust output"):
                    wallet._calculate_change(inputs, destinations, fee_rate=1)
