#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

import unittest
from zpywallet.address.btc import BitcoinAddress
from zpywallet.address.btctest import BitcoinTestAddress
from zpywallet.address.dash import DashAddress
from zpywallet.address.doge import DogecoinAddress
from zpywallet.address.eth import EthereumAddress
from zpywallet.address.ltc import LitecoinAddress

class TestBroadcast(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_btc_address(self):
        """Test fetching Bitcoin addresses."""
        b = BitcoinAddress(b'\xff', ['3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V', 'bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c'])
        b.sync()
        b.get_transaction_history()
        b.get_utxos()
        b.get_balance()

    def test_001_btctest_address(self):
        """Test fetching Bitcoin testnet addressses"""
        b = BitcoinTestAddress(b'\xff', ['2NDNwoqdNvJ2jkBD8B6VVxNntpuKR4tkTSz', 'tb1qtnl457a54cz5gq0zgyf4n2xt7n9uuqxzs8jwrp'])
        b.sync()
        b.get_transaction_history()
        b.get_utxos()
        b.get_balance()

    def test_002_dash_address(self):
        """Test fetching Dash addressses"""
        b = DashAddress(b'\xff', ['XbzLCqAv8rkYmky6uEsxibHRUbHZU2XCKg'])
        b.sync()
        b.get_transaction_history()
        b.get_utxos()
        b.get_balance()

    def test_003_doge_address(self):
        """Test fetching Dogecoin addressses"""
        b = DashAddress(b'\xff', ['DEhEbNiKjyQXSDCZGVh3iZSEBdLT6seLKA'])
        b.sync()
        b.get_transaction_history()
        b.get_utxos()
        b.get_balance()

    def test_004_eth_address(self):
        """Test fetching Ethereum addressses"""
        b = EthereumAddress(b'\xff', ['0x383d4669f177182f2c8c90cecd291190ea04edad'])
        #b.sync() # Do not sync, because that will take forever
        #b.get_transaction_history() # For similar reasons, do not get the transaction history
        b.get_block_height()
        b.get_balance()
    
    def test_003_ltc_address(self):
        """Test fetching Litecoin addressses"""
        b = LitecoinAddress(b'\xff', ['ltc1q9pw48v23gq9d2lqcss8yaqeh7fqzu4wrt6m6nr'])
        b.sync()
        b.get_transaction_history()
        b.get_utxos()
        b.get_balance()