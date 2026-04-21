#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for creating signed transactions."""

import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from eth_account import Account
from zpywallet.address import CryptoClient
from zpywallet.destination import Destination
from zpywallet.network import (
    BitcoinMainNet,
    BitcoinP2PKMainNet,
    BitcoinSegwitMainNet,
    BitcoinTestNet,
    EthereumMainNet,
)
from zpywallet.transactions.encode import (
    SIGHASH_ALL,
    assemble_segwit_payload,
    create_web3_transaction,
    create_signatures_legacy,
    create_signatures_segwit,
    create_transaction,
)
from zpywallet.utils.keys import PrivateKey, PublicKey
from zpywallet.utxo import UTXO
from zpywallet.nodes.eth import eth_nodes
from zpywallet.transactions.decode import parse_transaction, transaction_size_simple
from zpywallet.generated import wallet_pb2
from zpywallet.transaction import Transaction as WalletTransaction


class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def _make_utxo(self, private_key, address, network, txid, amount, index=0):
        return UTXO(
            None,
            None,
            _network=network,
            _internal_param_do_not_use={
                "txid": txid,
                "index": index,
                "amount": amount,
                "address": address,
                "private_key": private_key,
                "address_hash": private_key.public_key.hash160(),
                "nsequence": "ffffffff",
                "height": 1,
                "confirmed": True,
                "spent": False,
            },
        )

    def _destinations(self, network):
        return [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, network
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, network
            ),
        ]

    def test_000_legacy_sign(self):
        """Test creating Satoshi-like legacy transactions."""
        legacy_key = PrivateKey.from_int(1, network=BitcoinMainNet)
        utxo = self._make_utxo(
            legacy_key,
            legacy_key.public_key.base58_address(True),
            BitcoinMainNet,
            "11" * 32,
            50000,
        )

        signed_transaction = create_transaction(
            [utxo], self._destinations(BitcoinMainNet), network=BitcoinMainNet
        )
        parsed_transaction, _ = parse_transaction(signed_transaction, segwit=False)

        self.assertEqual(parsed_transaction["input_count"], 1)
        self.assertEqual(parsed_transaction["output_count"], 2)
        self.assertTrue(parsed_transaction["inputs"][0]["script_signature"])

    def test_001_fake_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions which have no segwit
        inputs, so falling back to legacy signing.
        """
        legacy_key = PrivateKey.from_int(1, network=BitcoinSegwitMainNet)
        utxo = self._make_utxo(
            legacy_key,
            legacy_key.public_key.base58_address(True),
            BitcoinSegwitMainNet,
            "22" * 32,
            50000,
        )

        signed_transaction = create_transaction(
            [utxo],
            self._destinations(BitcoinSegwitMainNet),
            network=BitcoinSegwitMainNet,
        )
        parsed_transaction, _ = parse_transaction(signed_transaction, segwit=False)

        self.assertNotEqual(signed_transaction[8:12], "0001")
        self.assertEqual(parsed_transaction["input_count"], 1)
        self.assertEqual(parsed_transaction["output_count"], 2)
        self.assertTrue(parsed_transaction["inputs"][0]["script_signature"])

    def test_002_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions, all segwit inputs."""
        segwit_key = PrivateKey.from_int(2, network=BitcoinSegwitMainNet)
        utxo = self._make_utxo(
            segwit_key,
            segwit_key.public_key.bech32_address(),
            BitcoinSegwitMainNet,
            "33" * 32,
            50000,
        )

        signed_transaction = create_transaction(
            [utxo],
            self._destinations(BitcoinSegwitMainNet),
            network=BitcoinSegwitMainNet,
        )
        parsed_transaction, _ = parse_transaction(signed_transaction, segwit=True)

        self.assertEqual(signed_transaction[8:12], "0001")
        self.assertEqual(parsed_transaction["input_count"], 1)
        self.assertEqual(parsed_transaction["output_count"], 2)
        self.assertEqual(len(parsed_transaction["inputs"][0]["witness_data"]), 2)
        self.assertEqual(parsed_transaction["inputs"][0]["script_signature"], "")

    def test_003_segwit_sign_partial(self):
        """Test creating Satoshi-like segwit transactions, mixed segwit and legacy inputs."""
        legacy_key = PrivateKey.from_int(1, network=BitcoinSegwitMainNet)
        segwit_key = PrivateKey.from_int(2, network=BitcoinSegwitMainNet)
        utxos = [
            self._make_utxo(
                legacy_key,
                legacy_key.public_key.base58_address(True),
                BitcoinSegwitMainNet,
                "44" * 32,
                25000,
            ),
            self._make_utxo(
                segwit_key,
                segwit_key.public_key.bech32_address(),
                BitcoinSegwitMainNet,
                "55" * 32,
                25000,
                index=1,
            ),
        ]

        signed_transaction = create_transaction(
            utxos,
            self._destinations(BitcoinSegwitMainNet),
            network=BitcoinSegwitMainNet,
        )
        parsed_transaction, _ = parse_transaction(signed_transaction, segwit=True)

        self.assertEqual(signed_transaction[8:12], "0001")
        self.assertEqual(parsed_transaction["input_count"], 2)
        self.assertEqual(parsed_transaction["output_count"], 2)
        self.assertEqual(parsed_transaction["inputs"][0]["witness_data"], [])
        self.assertEqual(len(parsed_transaction["inputs"][1]["witness_data"]), 2)

    def test_004_sign_with_change(self):
        """Test creating Satoshi-like transactions with change calculation"""
        segwit_key = PrivateKey.from_int(2, network=BitcoinSegwitMainNet)
        utxos = [
            self._make_utxo(
                segwit_key,
                segwit_key.public_key.bech32_address(),
                BitcoinSegwitMainNet,
                "66" * 32,
                50000,
            )
        ]
        destinations = self._destinations(BitcoinSegwitMainNet)

        temp_transaction = create_transaction(
            utxos, destinations, network=BitcoinSegwitMainNet
        )
        fee_rate = 1
        size = transaction_size_simple(temp_transaction)
        total_inputs = sum([i.amount(in_standard_units=False) for i in utxos])
        total_outputs = sum(
            [o.amount(in_standard_units=False) for o in destinations]
        )
        self.assertGreaterEqual(total_inputs, total_outputs + size * fee_rate)

        change_value = total_inputs - total_outputs - size * fee_rate
        self.assertGreater(change_value, 0)

        destinations.append(
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM",
                change_value,
                BitcoinSegwitMainNet,
                in_standard_units=False,
            )
        )
        signed_transaction = create_transaction(
            utxos, destinations, network=BitcoinSegwitMainNet
        )
        parsed_transaction, _ = parse_transaction(signed_transaction, segwit=True)

        self.assertEqual(parsed_transaction["output_count"], 3)
        self.assertIn(
            change_value, [output["value"] for output in parsed_transaction["outputs"]]
        )

    def test_005_eth_sign(self):
        """Test creating EVM Ethereum transactions."""

        class FakeMiddlewareOnion:
            def add(self, _middleware):
                return None

        class FakeEth:
            def __init__(self):
                self.account = Account
                self.gas_price = 1

            def set_gas_price_strategy(self, _strategy):
                return None

            def get_transaction_count(self, _address):
                return 7

            def estimate_gas(self, transaction):
                self.last_estimate = transaction
                return 21000

        class FakeWeb3:
            def __init__(self, _provider):
                self.eth = FakeEth()
                self.middleware_onion = FakeMiddlewareOnion()

        with patch("zpywallet.transactions.encode.web3.Web3", FakeWeb3):
            sender_address = Account.from_key("0x" + "11" * 32).address
            signed = create_web3_transaction(
                sender_address,
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                20,
                "0x" + "11" * 32,
                [{"url": "https://example.invalid"}],
                None,
                EthereumMainNet.CHAIN_ID,
            )

        recovered = Account.recover_transaction(bytes.fromhex(signed))
        self.assertEqual(recovered.lower(), sender_address.lower())

    def test_005a_eth_sign_supports_data_nonce_and_fee_overrides(self):
        class FakeMiddlewareOnion:
            def add(self, _middleware):
                return None

        class FakeAccount:
            def __init__(self):
                self.calls = []

            def sign_transaction(self, transaction, private_key):
                self.calls.append((transaction, private_key))
                return SimpleNamespace(raw_transaction=b"\x12\x34")

        class FakeEth:
            def __init__(self):
                self.account = FakeAccount()

            def set_gas_price_strategy(self, _strategy):
                return None

        class FakeWeb3:
            def __init__(self, _provider):
                self.eth = FakeEth()
                self.middleware_onion = FakeMiddlewareOnion()

        fake_web3 = FakeWeb3(None)
        with patch("zpywallet.transactions.encode.web3.Web3", return_value=fake_web3):
            sender_address = Account.from_key("0x" + "11" * 32).address
            signed = create_web3_transaction(
                sender_address,
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                20,
                "0x" + "11" * 32,
                [{"url": "https://example.invalid"}],
                25000,
                EthereumMainNet.CHAIN_ID,
                nonce=9,
                data="0x1234",
                max_fee_per_gas=30,
                max_priority_fee_per_gas=2,
            )

        self.assertEqual(signed, "1234")
        transaction, private_key = fake_web3.eth.account.calls[0]
        self.assertEqual(transaction["nonce"], 9)
        self.assertEqual(transaction["gas"], 25000)
        self.assertEqual(transaction["value"], 20)
        self.assertEqual(transaction["data"], bytes.fromhex("1234"))
        self.assertEqual(transaction["maxFeePerGas"], 30)
        self.assertEqual(transaction["maxPriorityFeePerGas"], 2)
        self.assertNotIn("gasPrice", transaction)
        self.assertEqual(private_key, bytes.fromhex("11" * 32))

    def test_005aa_eth_sign_rejects_mixed_fee_models(self):
        sender_address = Account.from_key("0x" + "11" * 32).address

        with self.assertRaisesRegex(ValueError, "Cannot mix gas_price"):
            create_web3_transaction(
                sender_address,
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                20,
                "0x" + "11" * 32,
                [{"url": "https://example.invalid"}],
                21000,
                EthereumMainNet.CHAIN_ID,
                gas_price=1,
                max_fee_per_gas=2,
                max_priority_fee_per_gas=1,
            )

    def test_005ab_eth_create_transaction_supports_contract_creation(self):
        sender_key = PrivateKey.from_int(1, network=EthereumMainNet)
        pseudo_input = UTXO(
            None,
            None,
            _network=EthereumMainNet,
            _internal_param_do_not_use={
                "address": sender_key.public_key.address(),
                "private_key": sender_key.to_hex(),
                "amount": 0,
                "height": 0,
            },
        )
        destinations = [Destination("", 0, EthereumMainNet, in_standard_units=False)]

        with patch(
            "zpywallet.transactions.encode.create_web3_transaction",
            return_value="beef",
        ) as signer:
            signed = create_transaction(
                [pseudo_input],
                destinations,
                network=EthereumMainNet,
                full_nodes=[{"url": "https://example.invalid"}],
                data="0x6000",
                nonce=3,
                gas=120000,
            )

        self.assertEqual(signed, "beef")
        _, kwargs = signer.call_args
        self.assertEqual(kwargs["data"], "0x6000")
        self.assertEqual(kwargs["nonce"], 3)
        self.assertEqual(kwargs["gas_price"], None)

    def test_005b_evm_transactions_reject_multiple_destinations(self):
        sender_key = PrivateKey.from_int(1, network=EthereumMainNet)
        pseudo_input = UTXO(
            None,
            None,
            _network=EthereumMainNet,
            _internal_param_do_not_use={
                "address": sender_key.public_key.address(),
                "private_key": sender_key.to_hex(),
                "amount": 0,
                "height": 0,
            },
        )
        destinations = [
            Destination(
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                0.00000002,
                EthereumMainNet,
            ),
            Destination(
                "0xd73e8e2ac0099169e7404f23c6caa94cf1884384",
                0.00000003,
                EthereumMainNet,
            ),
        ]

        with self.assertRaisesRegex(
            ValueError, "EVM transactions support exactly one destination"
        ):
            create_transaction([pseudo_input], destinations, network=EthereumMainNet)

    def test_005c_destination_accepts_raw_units(self):
        destination = Destination(
            "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM",
            25,
            BitcoinMainNet,
            in_standard_units=False,
        )

        self.assertEqual(destination.amount(in_standard_units=False), 25)
        self.assertEqual(destination.amount(), 25 / 1e8)

    def test_006_internal_legacy_sign(self):
        # This test case tests the internal signing methods to make sure that
        # They can sign arbitrary raw transactions properly.
        utxos = []
        p1 = PrivateKey.from_wif(
            "cThjSL4HkRECuDxUTnfAmkXFBEg78cufVBy3ZfEhKoxZo6Q38R5L",
            BitcoinTestNet,
        )

        bytes_1 = bytes.fromhex("0100000001")
        bytes_2_inputs = []
        bytes_3 = bytes.fromhex(
            "014062b007000000001976a914f86f0bc0a2232970ccdf4569815db500f126836188ac"
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "5e2383defe7efcbdc9fdd6dba55da148b206617bbb49e6bb93fce7bfbb459d44"
                )[::-1]
                + bytes.fromhex("01000000"),
                bytes.fromhex("01"),
                bytes.fromhex("ffffffff"),
                p1.public_key.p2pkh_script(),
                p1,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                None,
                BitcoinTestNet,
            ]
        )
        bytes_4 = bytes.fromhex("00000000")

        signed_transaction = create_signatures_legacy(
            bytes_1, bytes_2_inputs, bytes_3, bytes_4
        )
        correct_signed_transaction = "0100000001449d45bbbfe7fc93bbe649bb7b6106b248a15da5dbd6fdc9bdfc7efede83235e010000006b483045022100e15a8ead9013d1de55e71f195c9dc613483f07c8a0692a2144ffa90506436822022062bc9466b9e1941037fc23e1cfadf24c8833f96942beb8f4340df60d506f784b012103969a4ac9b1521cfae44a929a614193b0467a20e0a15973cae9ba1efb9627d830ffffffff014062b007000000001976a914f86f0bc0a2232970ccdf4569815db500f126836188ac00000000"
        print(signed_transaction)
        print(correct_signed_transaction)
        self.assertEqual(signed_transaction, correct_signed_transaction)

    def test_007_internal_segwit_sign(self):
        # This test case tests the internal signing methods to make sure that
        # They can sign arbitrary raw transactions properly.

        utxos = []
        p1 = PrivateKey.from_hex(
            "bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866",
            BitcoinP2PKMainNet,
        )
        p2 = PrivateKey.from_hex(
            "619c335025c7f4012e556c2a58b2506e30b8511b53ade95ea316fd8c3286feb9",
            BitcoinSegwitMainNet,
        )
        utxos.append(
            UTXO(
                None,
                None,
                _network=BitcoinP2PKMainNet,
                _internal_param_do_not_use={
                    "txid": "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f",
                    "index": 0,
                    "amount": 625000000,
                    "private_key": p1,
                    "address_hash": p1.public_key.hash160(),
                    "nsequence": "eeffffff",
                },
            )
        )
        utxos.append(
            UTXO(
                None,
                None,
                _network=BitcoinSegwitMainNet,
                _internal_param_do_not_use={
                    "txid": "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a",
                    "index": 1,
                    "amount": 600000000,
                    "private_key": p2,
                    "address_hash": p2.public_key.hash160(),
                    "nsequence": "ffffffff",
                },
            )
        )

        bytes_1 = bytes.fromhex("01000000000102")
        bytes_2_inputs = []
        bytes_3 = bytes.fromhex(
            "02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac"
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000"
                ),
                bytes.fromhex("00"),
                bytes.fromhex("eeffffff"),
                p1.public_key.p2pk_script(),
                p1,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                None,
                BitcoinP2PKMainNet,
            ]
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a01000000"
                ),
                bytes.fromhex("00"),
                bytes.fromhex("ffffffff"),
                p2.public_key.p2wpkh_script(),
                p2,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                assemble_segwit_payload(
                    utxos[1],
                    utxos,
                    bytes.fromhex("ffffffff"),
                    bytes_3[1:],
                    "11000000",
                ),
                BitcoinSegwitMainNet,
            ]
        )
        bytes_4 = bytes.fromhex("11000000")

        signed_transaction = create_signatures_segwit(
            bytes_1, bytes_2_inputs, bytes_3, bytes_4
        )
        correct_signed_transaction = "01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000494830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01eeffffffef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac0002483045022100befe22b0c41e05236670a718d129d8a007caaeff9be529451a827a10480e25ee022045692706920cdac497f49ee404d2e0abad71029c91e287bf1844559a544e55e30121025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee635711000000"
        print(signed_transaction)
        print(correct_signed_transaction)
        self.assertEqual(signed_transaction, correct_signed_transaction)

    def test_007a_segwit_payload_uses_little_endian_prevout_txids(self):
        segwit_key = PrivateKey.from_int(2, network=BitcoinSegwitMainNet)
        txid = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
        utxo = self._make_utxo(
            segwit_key,
            segwit_key.public_key.bech32_address(),
            BitcoinSegwitMainNet,
            txid,
            50000,
            index=2,
        )

        payload = assemble_segwit_payload(
            utxo,
            [utxo],
            bytes.fromhex("ffffffff"),
            bytes.fromhex("6a"),
        )

        prevout = bytes.fromhex(txid)[::-1] + (2).to_bytes(4, byteorder="little")
        expected_hash_prevouts = hashlib.sha256(
            hashlib.sha256(prevout).digest()
        ).digest()

        self.assertEqual(payload[4:36], expected_hash_prevouts)
        self.assertEqual(payload[68:100], bytes.fromhex(txid)[::-1])
        self.assertEqual(payload[100:104], (2).to_bytes(4, byteorder="little"))

    def test_008_transaction_wrapper_preserves_witness_metadata(self):
        transaction = wallet_pb2.Transaction()
        transaction.fee_metric = wallet_pb2.FeeMetric.Value("VBYTE")
        tx_input = transaction.btclike_transaction.inputs.add(
            txid="prev", index=0, amount=123, address="bc1qexample"
        )
        tx_input.witness_data.extend([b"first", b"second"])

        wrapped = WalletTransaction(transaction, BitcoinSegwitMainNet)

        self.assertNotIn("witness", wrapped.sat_inputs()[0])

        with_witness = wrapped.sat_inputs(include_witness=True)[0]
        self.assertEqual(with_witness["witness"], [b"first", b"second"])

        with_witness["witness"].append(b"mutated")
        self.assertEqual(
            wrapped.sat_inputs(include_witness=True)[0]["witness"],
            [b"first", b"second"],
        )

    def test_009_transaction_wrapper_returns_output_copies(self):
        transaction = wallet_pb2.Transaction()
        transaction.fee_metric = wallet_pb2.FeeMetric.Value("VBYTE")
        transaction.btclike_transaction.outputs.add(
            index=0, amount=321, address="bc1qoutput", spent=False
        )

        wrapped = WalletTransaction(transaction, BitcoinSegwitMainNet)
        outputs = wrapped.sat_outputs()
        outputs[0]["address"] = "mutated"

        self.assertEqual(wrapped.sat_outputs()[0]["address"], "bc1qoutput")

    def test_010_evm_transaction_wrapper_reports_stored_gas(self):
        transaction = wallet_pb2.Transaction()
        transaction.fee_metric = wallet_pb2.FeeMetric.Value("WEI")
        transaction.total_fee = 84000
        transaction.ethlike_transaction.txfrom = (
            "0xd73e8e2ac0099169e7404f23c6caa94cf1884384"
        )
        transaction.ethlike_transaction.txto = (
            "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6"
        )
        transaction.ethlike_transaction.amount = 25
        transaction.ethlike_transaction.gas = 21000

        wrapped = WalletTransaction(transaction, EthereumMainNet)

        self.assertEqual(wrapped.evm_gas(), 21000)
        self.assertEqual(wrapped.total_fee(in_standard_units=False), (84000, "wei"))

    def test_011_evm_transaction_wrapper_normalizes_canonical_txid(self):
        transaction = wallet_pb2.Transaction()
        transaction.txid = "AB" * 32
        transaction.fee_metric = wallet_pb2.FeeMetric.Value("WEI")

        wrapped = WalletTransaction(transaction, EthereumMainNet)

        self.assertEqual(wrapped.txid(), "0x" + ("ab" * 32))
