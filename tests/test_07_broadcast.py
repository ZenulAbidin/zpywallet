#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for transaction broadcasting."""

import asyncio
import hashlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from zpywallet.broadcast import broadcast_transaction, tx_hash
from zpywallet.broadcast.bcy.blockcypher import broadcast_transaction_bcy_blockcypher
from zpywallet.broadcast.btc.all import tx_hash_btc
from zpywallet.broadcast.btc.bitaps import broadcast_transaction_btc_bitaps
from zpywallet.broadcast.btc.blockstream import broadcast_transaction_btc_blockstream
from zpywallet.broadcast.btc.blockcypher import broadcast_transaction_btc_blockcypher
from zpywallet.broadcast.btc.esplora import broadcast_transaction_btc_esplora
from zpywallet.broadcast.btc.mempool_space import (
    broadcast_transaction_btc_mempool_space,
)
from zpywallet.broadcast.btctest.bitaps import broadcast_transaction_btctest_bitaps
from zpywallet.broadcast.btctest.esplora import (
    broadcast_transaction_btctest_esplora,
)
from zpywallet.errors import NetworkException
from zpywallet import network
from zpywallet.broadcast.eth.all import broadcast_transaction_eth, tx_hash_eth
from zpywallet.broadcast.btc.all import broadcast_transaction_btc
from zpywallet.broadcast.eth.blockcypher import broadcast_transaction_eth_blockcypher
from zpywallet.broadcast.eth.fullnode import broadcast_transaction_eth_generic
from zpywallet.broadcast.eth.mew import broadcast_transaction_eth_mew

RUN_LIVE_TESTS = os.getenv("ZPYWALLET_RUN_LIVE_TESTS") == "1"


class TestBroadcast(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_000_btc_transaction(self):
        """Test broadcasting Bitcoin transactions."""
        rawtx = b"010000000113f3b5446192eeb85c0f7ca64c12196c26314d27b5ab6a976d560cb134ffa82f020000006b483045022100deb556a5c301696f5def1888e54e8c1227caeb3ed4ae7b1c665af79174f50ab702201a59bba811554bd66fa003606ba852bf17699f38c6b1c3f8628f36c9d193a081012102245a4ecd8ad47f171f90c6d4a4f929052814d844e4d8c112bbf799aedc1b8555ffffffff061953cb010000000017a9145bf7f29863984cd9c8ff321a6d93d6344c7c055287102cf604000000001976a9148e09dee91c997fd306030ad7a1c46f17dcd51fdd88ace00f97000000000017a914ecd0679169813020faa97b418be8e79098c1cd55871595c1000000000017a914b61a3c9897d3d539aee6ad7327dfbd2192103e6287a4b62100000000001976a9144954c267b47bd1f864e627ca5b9c82b1fde8966188ac9e41a409000000001976a9141199950f4896dbbbd5ddc833092f5458b5f3154888ac00000000"
        broadcast_transaction(
            rawtx,
            network.BitcoinSegwitMainNet,
            rpc_nodes=[{"url": "https://rpc.coinsdo.net/btc"}],
        )

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_001_btctest_transaction(self):
        """Test broadcasting Bitcoin testnet transactions."""
        rawtx = b"010000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff5203fcc21f3a205468697320626c6f636b20776173206d696e65642077697468206120636172626f6e206e6567617469766520706f77657220736f75726365201209687a2009092009020ddf01c35316000000ffffffff02f90295000000000017a9141320e6542e2146ea486700f4091aa793e7360788870000000000000000266a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf90120000000000000000000000000000000000000000000000000000000000000000000000000"
        broadcast_transaction(rawtx, network.BitcoinSegwitTestNet)

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_002_dash_transaction(self):
        """Test broadcasting Dash transactions."""
        rawtx = b"200000004a9374eafe65822799e5cbf4eed5be21c071cba0667932d4893e1d0bed1a97b10010000006a473044022014605459fe68bf850c136af8fa9abe9fd981e00c5c30e465b2e154235674b929022014344ac6e27cd4c0d5f7ee792bacd9ac70936d6ae939734c823f24c05e11cbb2812102f805604337bf46b0039e59fdc51b51fc92de581ccdebaede826de042e93eba54ffffffff9ad014138a94d93878da074427db6f57bcf2159d29452240b2716736c5440896040000006a47304402204b7bc3a30b00d170bd0b1e59b470858465c6a9a8bfdc44060ab8edfd62bb4d85022030ccb68a642eb6cc0eb441b0203629fccba0f2e4133ea4438a886222a24a1c83812103b21b59a13bd1dfe6aac94a7298bc0e166ead0cd695bcc0019a61769796c41f0cffffffffe9b4205a9474b00cc0dfb08d38fc8a71f3cc40577b7767ab9fcb1b27b6ee21c9030000006a47304402205098ee6736e0051a11bf9bf8901dc08afe34449aa9b3ae73742a35157f1d1eff022038756b5c6e2c1721d5df25ebcdf50c80affa7630718dd3b8996a0483974c03dc812102e4580b97988f21ac72c64399b9665b6aeb7a301835bf70e38afdf4f1532f1ca3ffffffff8e35233a4d82811685f4b303550b84d2aea254aa6d1343d0db678432b11a70f0030000006a473044022064dc27e1056ee94263cbd419fcaf861e3f61cf60efd1a170f4c715d60c8012fa0220598fbbc905fe287c0c8906325949e9f01261cc14d5631e647dc51fc4711178d6012103deee52818000848677e693474c1bf20595dcb020f22cea73deda5072c71bb457ffffffff04e8e4f505000000001976a9140c3f6f654aecd8c6aec5f15b81b6b6ec6e08fbcd88ace8e4f505000000001976a914308330067aae3f9e58b8050fe3b64e03db74969788ace8e4f505000000001976a91439e029f1661324958090f50447effc367a349d9a88ace8e4f505000000001976a91456403a78f0839eb00ae56704d48d6ca78b1bf8fa88ac00000000"
        broadcast_transaction(rawtx, network.DashMainNet)

    # test 003 reserved for dashtest

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_004_doge_transaction(self):
        """Test broadcasting Dogecoin transactions."""
        rawtx = b"01000000011d1b301834aed95349bf7834ec8875184c841e727b86a18df757779789d82fc5000000004847304402203afab23c4deaa6c4200bb63b52044e5de7e8efd519999c308039ddb624f1dc8a0220303344a4030297db3691d167bf17a426370bb4e33c6386968d1fbc5550a7479b01feffffff013037a914e90000001976a914648bfbc48ade652cfe0303b90a04e1a9cd71363b88ac46a33d00"
        broadcast_transaction(rawtx, network.DogecoinMainNet)

    # test 005 reserved for dogetest

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_006_eth_transaction(self):
        """Test broadcasting Ethereum transactions."""
        rawtx = b"0x02f87401820189840426229985050abb4114825208947322ef15f695d2adae83ddd38b722c156277bf4f871057acf5f7800080c001a0f17ee75e1f64ddd8d98318f18a17521fcbb108b832bb2cc8270118e9613d251ca057b36d360f0f477a4fa8ecda3fc424d5ebe1beaaa89eea04354233e5927e5116"
        broadcast_transaction(rawtx, network.EthereumMainNet)

    @unittest.skipUnless(RUN_LIVE_TESTS, "live broadcast tests are opt-in")
    def test_007_ltc_transaction(self):
        """Test broadcasting Litecoin transactions."""
        rawtx = b"0100000001aa95cd5b6db81f5ea45fcf73baed68e3981b908d9b871224ecee610f0653597d010000006a47304402207bd002f3824279d0b9439bb098cf699fdd991b03ef4f8fa5a7cf519fb1792bd20220623b53259ffc7a340b11a577a6502cccd5a9a6e79fbaf0a8ba3da5038619494f0121022de5d23d6c035822456e06cf9b181c12e097dade9ca06dd2f2b57dc70e7d463cfeffffff0217e353a8000000001976a9140c96f80a6b3b6d8db7ce70ef95969946f6fcabd688ac8091e305000000001976a914d0c065845120427fd774be5425f0e760b24abd1e88acda961800"
        broadcast_transaction(rawtx, network.LitecoinMainNet)

    # test 008 reserved for ltctest

    def test_008_eth_tx_hash(self):
        rawtx = b"0x02f87401820189840426229985050abb4114825208947322ef15f695d2adae83ddd38b722c156277bf4f871057acf5f7800080c001a0f17ee75e1f64ddd8d98318f18a17521fcbb108b832bb2cc8270118e9613d251ca057b36d360f0f477a4fa8ecda3fc424d5ebe1beaaa89eea04354233e5927e5116"
        self.assertEqual(
            tx_hash_eth(rawtx),
            "0x8266a740d79310062e1c8be67bb2808edf53d6fb6b01e6653a2c10a8d2682b20",
        )
        self.assertEqual(tx_hash(rawtx, network.EthereumMainNet), tx_hash_eth(rawtx))

    def test_008b_btc_tx_hash_accepts_hex_and_raw_bytes(self):
        rawtx_hex = (
            "010000000113f3b5446192eeb85c0f7ca64c12196c26314d27b5ab6a976d560cb134ffa82f"
            "020000006b483045022100deb556a5c301696f5def1888e54e8c1227caeb3ed4ae7b1c665a"
            "f79174f50ab702201a59bba811554bd66fa003606ba852bf17699f38c6b1c3f8628f36c9d1"
            "93a081012102245a4ecd8ad47f171f90c6d4a4f929052814d844e4d8c112bbf799aedc1b85"
            "55ffffffff061953cb010000000017a9145bf7f29863984cd9c8ff321a6d93d6344c7c055287"
            "102cf604000000001976a9148e09dee91c997fd306030ad7a1c46f17dcd51fdd88ace00f9700"
            "0000000017a914ecd0679169813020faa97b418be8e79098c1cd55871595c1000000000017a9"
            "14b61a3c9897d3d539aee6ad7327dfbd2192103e6287a4b62100000000001976a9144954c267"
            "b47bd1f864e627ca5b9c82b1fde8966188ac9e41a409000000001976a9141199950f4896dbbb"
            "d5ddc833092f5458b5f3154888ac00000000"
        )
        expected = hashlib.sha256(
            hashlib.sha256(bytes.fromhex(rawtx_hex)).digest()
        ).digest()[::-1].hex()

        self.assertEqual(tx_hash_btc(rawtx_hex), expected)
        self.assertEqual(tx_hash_btc(rawtx_hex.encode()), expected)
        self.assertEqual(tx_hash_btc(bytes.fromhex(rawtx_hex)), expected)
        self.assertEqual(
            tx_hash(rawtx_hex.encode(), network.BitcoinSegwitMainNet), expected
        )

    def test_009_eth_generic_broadcast_uses_modern_web3_api(self):
        class FakeHash:
            def hex(self):
                return "0xabc123"

        class FakeEth:
            def __init__(self):
                self.sent = None

            def send_raw_transaction(self, payload):
                self.sent = payload
                return FakeHash()

        class FakeWeb3:
            def __init__(self, _provider):
                self.eth = FakeEth()

            @staticmethod
            def HTTPProvider(url):
                return url

        with patch("zpywallet.broadcast.eth.fullnode.Web3", FakeWeb3):
            txid = __import__(
                "asyncio"
            ).run(
                broadcast_transaction_eth_generic(
                    "deadbeef", url="https://example.invalid"
                )
            )

        self.assertEqual(txid, "0xabc123")

    def test_010_broadcast_transaction_returns_async_result(self):
        async def fake_eth_broadcast(_tx, **_kwargs):
            return "ok"

        with patch(
            "zpywallet.broadcast.broadcast.broadcast_transaction_eth",
            fake_eth_broadcast,
        ):
            self.assertEqual(
                broadcast_transaction(b"0x00", network.EthereumMainNet), "ok"
            )

    def test_011_eth_tx_hash_accepts_signed_transaction_like_objects(self):
        signed = SimpleNamespace(raw_transaction=bytes.fromhex("deadbeef"))

        self.assertEqual(tx_hash_eth(signed), tx_hash_eth("0xdeadbeef"))

    def test_012_eth_broadcast_normalizes_signed_transaction_objects(self):
        captured = []

        async def fake_blockcypher(raw_transaction_hex):
            captured.append(("blockcypher", raw_transaction_hex))
            return "ok"

        async def fake_mew(raw_transaction_hex):
            captured.append(("mew", raw_transaction_hex))
            return "ok"

        async def fake_generic(raw_transaction_hex, **kwargs):
            captured.append(("generic", raw_transaction_hex, kwargs["url"]))
            return "ok"

        with patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_blockcypher",
            fake_blockcypher,
        ), patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_mew", fake_mew
        ), patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_generic",
            fake_generic,
        ), patch("zpywallet.broadcast.eth.all.eth_nodes", []):
            results = asyncio.run(
                broadcast_transaction_eth(
                    SimpleNamespace(raw_transaction=bytes.fromhex("deadbeef")),
                    rpc_nodes=[{"url": "https://example.invalid"}],
                )
            )

        self.assertCountEqual(
            captured,
            [
                ("blockcypher", "deadbeef"),
                ("mew", "deadbeef"),
                ("generic", "deadbeef", "https://example.invalid"),
            ],
        )
        self.assertEqual(results, ["ok", "ok", "ok"])

    def test_013_btc_broadcast_returns_provider_results(self):
        async def fake_success(raw_transaction_hex, **kwargs):
            self.assertEqual(raw_transaction_hex, "deadbeef")
            return kwargs.get("url", "ok")

        with patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_bitaps",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_blockchain_info",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_blockchair",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_blockcypher",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_blockstream",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_mempool_space",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_smartbit",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_viabtc",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_full_node",
            fake_success,
        ), patch(
            "zpywallet.broadcast.btc.all.broadcast_transaction_btc_esplora",
            fake_success,
        ), patch("zpywallet.broadcast.btc.all.btc_nodes", []), patch(
            "zpywallet.broadcast.btc.all.btc_esplora_nodes", []
        ):
            results = asyncio.run(
                broadcast_transaction_btc(
                    "deadbeef",
                    rpc_nodes=[{"url": "https://rpc.example.invalid"}],
                    esplora_nodes=[{"url": "https://esplora.example.invalid"}],
                )
            )

        self.assertEqual(
            results,
            [
                "ok",
                "ok",
                "ok",
                "ok",
                "ok",
                "ok",
                "ok",
                "ok",
                "https://rpc.example.invalid",
                "https://esplora.example.invalid",
            ],
        )

    def test_014_eth_broadcast_raises_when_all_providers_fail(self):
        async def fake_failure(*_args, **_kwargs):
            raise NetworkException("boom")

        with patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_blockcypher",
            fake_failure,
        ), patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_mew",
            fake_failure,
        ), patch(
            "zpywallet.broadcast.eth.all.broadcast_transaction_eth_generic",
            fake_failure,
        ), patch("zpywallet.broadcast.eth.all.eth_nodes", []):
            with self.assertRaises(NetworkException):
                asyncio.run(
                    broadcast_transaction_eth(
                        "deadbeef",
                        rpc_nodes=[{"url": "https://example.invalid"}],
                    )
                )

    def test_015_eth_blockcypher_returns_canonical_txid_when_body_has_no_hash(self):
        class FakeResponse:
            status_code = 201
            text = ""

            @staticmethod
            def json():
                return {"status": "1"}

        with patch(
            "zpywallet.broadcast.eth.blockcypher.requests.post",
            return_value=FakeResponse(),
        ):
            txid = asyncio.run(broadcast_transaction_eth_blockcypher("deadbeef"))

        self.assertEqual(txid, tx_hash_eth("deadbeef"))

    def test_016_eth_mew_raises_on_provider_error_payload(self):
        class FakeResponse:
            status_code = 200
            text = "bad"

            @staticmethod
            def json():
                return {"status": "0", "message": "bad"}

        with patch(
            "zpywallet.broadcast.eth.mew.requests.post",
            return_value=FakeResponse(),
        ):
            with self.assertRaises(NetworkException):
                asyncio.run(broadcast_transaction_eth_mew("deadbeef"))

    def test_017_eth_mew_returns_canonical_txid_when_body_has_no_hash(self):
        class FakeResponse:
            status_code = 200
            text = ""

            @staticmethod
            def json():
                return {"status": "1"}

        with patch(
            "zpywallet.broadcast.eth.mew.requests.post",
            return_value=FakeResponse(),
        ):
            txid = asyncio.run(broadcast_transaction_eth_mew("deadbeef"))

        self.assertEqual(txid, tx_hash_eth("deadbeef"))

    def test_018_btc_blockcypher_returns_canonical_txid_on_success(self):
        rawtx = "01000000"

        class FakeResponse:
            status_code = 201
            text = ""

        with patch(
            "zpywallet.broadcast.btc.blockcypher.requests.post",
            return_value=FakeResponse(),
        ):
            txid = asyncio.run(broadcast_transaction_btc_blockcypher(rawtx))

        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_019_btc_esplora_returns_canonical_txid_on_success(self):
        rawtx = "01000000"

        class FakeResponse:
            status_code = 200
            text = ""

        with patch(
            "zpywallet.broadcast.btc.esplora.requests.post",
            return_value=FakeResponse(),
        ):
            txid = asyncio.run(
                broadcast_transaction_btc_esplora(
                    rawtx, url="https://esplora.example.invalid"
                )
            )

        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_020_bcy_blockcypher_returns_canonical_txid_on_success(self):
        rawtx = "01000000"

        class FakeResponse:
            status_code = 201
            text = ""

        with patch(
            "zpywallet.broadcast.bcy.blockcypher.requests.post",
            return_value=FakeResponse(),
        ):
            txid = asyncio.run(broadcast_transaction_bcy_blockcypher(rawtx))

        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_021_btc_bitaps_uses_mainnet_endpoint(self):
        rawtx = "01000000"
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        with patch("zpywallet.broadcast.btc.bitaps.requests.post", fake_post):
            txid = asyncio.run(broadcast_transaction_btc_bitaps(rawtx))

        self.assertEqual(captured["url"], "https://api.bitaps.com/btc/v1/create/tx/push")
        self.assertEqual(captured["kwargs"]["json"], {"hex": rawtx})
        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_022_btctest_bitaps_stays_on_testnet_endpoint(self):
        rawtx = "01000000"
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        with patch("zpywallet.broadcast.btctest.bitaps.requests.post", fake_post):
            txid = asyncio.run(broadcast_transaction_btctest_bitaps(rawtx))

        self.assertEqual(
            captured["url"], "https://api.bitaps.com/btc/testnet/v1/create/tx/push"
        )
        self.assertEqual(captured["kwargs"]["json"], {"hex": rawtx})
        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_023_btc_blockstream_posts_raw_hex_body(self):
        rawtx = "01000000"
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        with patch("zpywallet.broadcast.btc.blockstream.requests.post", fake_post):
            txid = asyncio.run(broadcast_transaction_btc_blockstream(rawtx))

        self.assertEqual(captured["url"], "https://blockstream.info/api/tx")
        self.assertEqual(captured["kwargs"]["data"], rawtx)
        self.assertEqual(
            captured["kwargs"]["headers"], {"Content-Type": "text/plain"}
        )
        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_024_btc_mempool_space_posts_raw_hex_body(self):
        rawtx = "01000000"
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        with patch("zpywallet.broadcast.btc.mempool_space.requests.post", fake_post):
            txid = asyncio.run(broadcast_transaction_btc_mempool_space(rawtx))

        self.assertEqual(captured["url"], "https://mempool.space/api/tx")
        self.assertEqual(captured["kwargs"]["data"], rawtx)
        self.assertEqual(
            captured["kwargs"]["headers"], {"Content-Type": "text/plain"}
        )
        self.assertEqual(txid, tx_hash_btc(rawtx))

    def test_025_btctest_esplora_posts_raw_hex_body(self):
        rawtx = "01000000"
        captured = {}

        class FakeResponse:
            status_code = 200
            text = ""

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        with patch("zpywallet.broadcast.btctest.esplora.requests.post", fake_post):
            txid = asyncio.run(
                broadcast_transaction_btctest_esplora(
                    rawtx, url="https://esplora.example.invalid"
                )
            )

        self.assertEqual(captured["url"], "https://esplora.example.invalid/api/tx")
        self.assertEqual(captured["kwargs"]["data"], rawtx)
        self.assertEqual(
            captured["kwargs"]["headers"], {"Content-Type": "text/plain"}
        )
        self.assertEqual(txid, tx_hash_btc(rawtx))
