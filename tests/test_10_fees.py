#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for fee estimation."""

import unittest
from zpywallet.errors import NetworkException
from zpywallet.fees.btc import BitcoinFeeEstimator
from zpywallet.fees.ltc import LitecoinFeeEstimator
from zpywallet.fees.dash import DashFeeEstimator
from zpywallet.fees.doge import DogecoinFeeEstimator
from zpywallet.fees.eth import EthereumFeeEstimator


class FailingFeeProvider:
    def get_fee_rate(self):
        raise NetworkException("provider unavailable")


class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_btc_fee_estimator(self):
        """Test estimating Bitcoin fees."""
        b = BitcoinFeeEstimator()
        b.get_fee_rate()

    def test_001_ltc_fee_estimator(self):
        """Test estimating Litecoin fees."""
        b = LitecoinFeeEstimator()
        b.get_fee_rate()

    def test_002_dash_fee_estimator(self):
        """Test estimating Dash fees."""
        b = DashFeeEstimator()
        b.get_fee_rate()

    def test_003_doge_fee_estimator(self):
        """Test estimating Dogecoin fees."""
        b = DogecoinFeeEstimator()
        b.get_fee_rate()

    def test_004_eth_fee_estimator(self):
        """Test estimating Ethereum fees."""
        b = EthereumFeeEstimator()
        # print(b.estimate_gas())

    def test_005_ltc_fee_estimator_uses_minimum_relay_fallback(self):
        """Litecoin fee estimation should stay usable when providers are down."""
        b = LitecoinFeeEstimator(fullnode_endpoints=[], blockcypher_tokens=[])
        b.provider_list = [FailingFeeProvider()]
        self.assertEqual(b.get_fee_rate(), 1)

    def test_006_dash_fee_estimator_uses_minimum_relay_fallback(self):
        """Dash fee estimation should stay usable when providers are down."""
        b = DashFeeEstimator(fullnode_endpoints=[], blockcypher_tokens=[])
        b.provider_list = [FailingFeeProvider()]
        self.assertEqual(b.get_fee_rate(), 1)
