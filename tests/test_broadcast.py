#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for `zpywallet` package."""

import binascii
import unittest
from zpywallet.broadcast import broadcast_transaction
from zpywallet import network

class TestBroadcast(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_btc_transaction(self):
        """Test broadcasting bitcoin transactions."""
        rawtx = "010000000113f3b5446192eeb85c0f7ca64c12196c26314d27b5ab6a976d560cb134ffa82f020000006b483045022100deb556a5c301696f5def1888e54e8c1227caeb3ed4ae7b1c665af79174f50ab702201a59bba811554bd66fa003606ba852bf17699f38c6b1c3f8628f36c9d193a081012102245a4ecd8ad47f171f90c6d4a4f929052814d844e4d8c112bbf799aedc1b8555ffffffff061953cb010000000017a9145bf7f29863984cd9c8ff321a6d93d6344c7c055287102cf604000000001976a9148e09dee91c997fd306030ad7a1c46f17dcd51fdd88ace00f97000000000017a914ecd0679169813020faa97b418be8e79098c1cd55871595c1000000000017a914b61a3c9897d3d539aee6ad7327dfbd2192103e6287a4b62100000000001976a9144954c267b47bd1f864e627ca5b9c82b1fde8966188ac9e41a409000000001976a9141199950f4896dbbbd5ddc833092f5458b5f3154888ac00000000"
        errors = broadcast_transaction(rawtx, network.BitcoinSegwitMainNet)
        print(errors)