# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

from os import urandom
from random import randrange
from typing import List

from zpywallet.utxo import UTXO

from .destination import Destination

from .mnemonic import Mnemonic
from .utils.bip32 import (
    HDWallet
)

from .utils.keys import (
    PrivateKey
)
from .transactions.encode import create_transaction
from .transactions.decode import transaction_size_simple
from .broadcast import broadcast_transaction

from .generated import wallet_pb2

from .network import (
    BitcoinSegwitMainNet,
    BitcoinMainNet,
    BitcoinSegwitTestNet,
    BitcoinTestNet,
    LitecoinSegwitMainNet,
    LitecoinMainNet,
    LitecoinBTCSegwitMainNet,
    LitecoinBTCMainNet,
    LitecoinSegwitTestNet,
    LitecoinTestNet,
    EthereumMainNet,
    DogecoinMainNet,
    DogecoinBTCMainNet,
    DogecoinTestNet,
    DashMainNet,
    DashInvertedTestNet,
    DashBTCMainNet,
    DashTestNet,
    DashInvertedMainNet,
    BitcoinCashMainNet,
    BlockcypherTestNet
)

from .address.bcy import BCYAddress
from .address.btc import BitcoinAddress
from .address.btctest import BitcoinTestAddress
from .address.dash import DashAddress
from .address.doge import DogecoinAddress
from .address.eth import EthereumAddress
from .address.ltc import LitecoinAddress

from .utils.aes import decrypt, encrypt

from .transaction import Transaction

def generate_mnemonic(strength=128):
    """Creates a new seed phrase of the specified length"""
    if strength % 32 != 0:
        raise ValueError("strength must be a multiple of 32")
    if strength < 128 or strength > 256:
        raise ValueError("strength should be >= 128 and <= 256")
    entropy = urandom(strength // 8)
    mne = Mnemonic(language='english')
    mnemonic = mne.to_mnemonic(entropy)
    return mnemonic


def create_wallet(mnemonic=None, network=BitcoinSegwitMainNet, strength=128) -> HDWallet:
    """Generate a new wallet class from a mnemonic phrase, optionally randomly generated

    Args:
    :param mnemonic: The key to use to generate this wallet. It may be a long
        string. Do not use a phrase from a book or song, as that will
        be guessed and is not secure. My advice is to not supply this
        argument and let me generate a new random key for you.
    :param network: The network to create this wallet for
    :param children: Create this many child addresses for this wallet. Default
        is 10, You should not use the master private key itself for sending
        or receiving funds, as a best practice.

    Return:
        HDWallet: a wallet class
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """
    if mnemonic is None:
        return HDWallet.from_random(strength=strength, network=network)
    else:
        return HDWallet.from_mnemonic(mnemonic=mnemonic, network=network)


def create_keypair(network=BitcoinSegwitMainNet):
    """Generates a random private/public keypair.

    Args:
    :param network: The network to create this wallet for

    Return:
        PrivateKey, PublicKey: a tuple of a private key and public key.
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """

    random_bytes = urandom(32)
    prv = PrivateKey(random_bytes, network=network)
    pub = prv.public_key
    return prv, pub

class Wallet:
    """Data class representing a cryptocurrency wallet."""

    def __init__(self, network, seed_phrase, password, receive_gap_limit=10000, change_gap_limit=1000,
                  derivation_path = None, _with_wallet=True, **kwargs):
        
        fullnode_endpoints = kwargs.get('fullnode_endpoints')
        esplora_endpoints = kwargs.get('esplora_endpoints')
        blockcypher_tokens = kwargs.get('blockcypher_tokens')

        self.network = network
        if not derivation_path:
            derivation_path = network.BIP32_SEGWIT_PATH if network.BIP32_SEGWIT_PATH else network.BIP32_PATH

        
        if _with_wallet:
            self.wallet = wallet_pb2.Wallet()
            self.wallet.SerializeToString()
            self.wallet.receive_gap_limit = receive_gap_limit
            self.wallet.change_gap_limit = change_gap_limit
            self.wallet.height = 0

            if type(derivation_path) is str:
                self.wallet.derivation_path = derivation_path
            else:
                raise ValueError("Invalid derivation path")
            
            # We do not save the password. Instead, we are going to generate a base64-encrypted
            # serialization of this wallet file using the password.
            self.wallet.encrypted_seed_phrase = encrypt(seed_phrase, password) # AES-256-CBC encryption

            # Generate addresses and keys
            hdwallet = HDWallet.from_mnemonic(mnemonic=seed_phrase, network=network)

            # Set properties
            if network == BitcoinSegwitMainNet:
                self.wallet.network = wallet_pb2.BITCOIN_SEGWIT_MAINNET
            elif network == BitcoinMainNet:
                self.wallet.network = wallet_pb2.BITCOIN_MAINNET
            elif network == BitcoinSegwitTestNet:
                self.wallet.network = wallet_pb2.BITCOIN_SEGWIT_TESTNET
            elif network == BitcoinTestNet:
                self.wallet.network = wallet_pb2.BITCOIN_TESTNET
            elif network == LitecoinSegwitMainNet:
                self.wallet.network = wallet_pb2.LITECOIN_SEGWIT_MAINNET
            elif network == LitecoinMainNet:
                self.wallet.network = wallet_pb2.LITECOIN_MAINNET
            elif network == LitecoinBTCSegwitMainNet:
                self.wallet.network = wallet_pb2.LITECOIN_BTC_SEGWIT_MAINNET
            elif network == LitecoinBTCMainNet:
                self.wallet.network = wallet_pb2.LITECOIN_BTC_MAINNET
            elif network == LitecoinSegwitTestNet:
                self.wallet.network = wallet_pb2.LITECOIN_SEGWIT_TESTNET
            elif network == LitecoinTestNet:
                self.wallet.network = wallet_pb2.LITECOIN_TESTNET
            elif network == EthereumMainNet:
                self.wallet.network = wallet_pb2.ETHEREUM_MAINNET
            elif network == DogecoinMainNet:
                self.wallet.network = wallet_pb2.DOGECOIN_MAINNET
            elif network == DogecoinBTCMainNet:
                self.wallet.network = wallet_pb2.DOGECOIN_BTC_MAINNET
            elif network == DogecoinTestNet:
                self.wallet.network = wallet_pb2.DOGECOIN_TESTNET
            elif network == DashMainNet:
                self.wallet.network = wallet_pb2.DASH_MAINNET
            elif network == DashInvertedMainNet:
                self.wallet.network = wallet_pb2.DASH_INVERTED_MAINNET
            elif network == DashBTCMainNet:
                self.wallet.network = wallet_pb2.DASH_BTC_MAINNET
            elif network == DashTestNet:
                self.wallet.network = wallet_pb2.DASH_TESTNET
            elif network == DashInvertedTestNet:
                self.wallet.network = wallet_pb2.DASH_INVERTED_TESTNET
            elif network == BitcoinCashMainNet:
                self.wallet.network = wallet_pb2.BITCOIN_CASH_MAINNET
            elif network == BlockcypherTestNet:
                self.wallet.network = wallet_pb2.BLOCKCYPHER_TESTNET
            else:
                raise ValueError("Unkown network")

            if fullnode_endpoints is not None:
                self.wallet.fullnode_endpoints.extend(fullnode_endpoints)

            if esplora_endpoints is not None:
                self.wallet.esplora_endpoints.extend(esplora_endpoints)

            if blockcypher_tokens is not None:
                self.wallet.blockcypher_tokens.extend(blockcypher_tokens)
                
            for i in range(0, receive_gap_limit):
                privkey = hdwallet.get_child_for_path(f"{derivation_path}0/{i}").private_key
                pubkey = privkey.public_key

                # Add an Address
                address = self.wallet.addresses.add()
                address.address = pubkey.address()
                address.pubkey = pubkey.to_hex()
                address.privkey = privkey.to_wif()

            # for i in range(0, change_gap_limit):
            #     privkey = hdwallet.get_child_for_path(f"{derivation_path}1/{i}").private_key
            #     pubkey = privkey.public_key
                
            #     # Add an Address
            #     address = self.wallet.addresses.add()
            #     address.address = pubkey.address()
            #     address.pubkey = pubkey.to_hex()
            #     address.privkey = privkey.to_wif()
            

    @classmethod
    def load_wallet(cls, data: bytes):
        self = cls(_with_wallet=False)
        self.wallet = wallet_pb2.Wallet.ParseFromString(data)

        if self.wallet.network == wallet_pb2.BITCOIN_SEGWIT_MAINNET:
            network = BitcoinSegwitMainNet
        if self.wallet.network == wallet_pb2.BITCOIN_MAINNET:
            network = BitcoinMainNet
        if self.wallet.network == wallet_pb2.BITCOIN_SEGWIT_TESTNET:
            network = BitcoinSegwitTestNet
        if self.wallet.network == wallet_pb2.BITCOIN_TESTNET:
            network = BitcoinTestNet
        if self.wallet.network == wallet_pb2.LITECOIN_SEGWIT_MAINNET:
            network = LitecoinSegwitMainNet
        if self.wallet.network == wallet_pb2.LITECOIN_MAINNET:
            network = LitecoinMainNet
        if self.wallet.network == wallet_pb2.LITECOIN_BTC_SEGWIT_MAINNET:
            network = LitecoinBTCSegwitMainNet
        if self.wallet.network == wallet_pb2.LITECOIN_BTC_MAINNET:
            network = LitecoinBTCMainNet
        if self.wallet.network == wallet_pb2.LITECOIN_SEGWIT_TESTNET:
            network = LitecoinSegwitTestNet
        if self.wallet.network == wallet_pb2.LITECOIN_TESTNET:
            network = LitecoinTestNet
        if self.wallet.network == wallet_pb2.ETHEREUM_MAINNET:
            network = EthereumMainNet
        if self.wallet.network == wallet_pb2.DOGECOIN_MAINNET:
            network = DogecoinMainNet
        if self.wallet.network == wallet_pb2.DOGECOIN_BTC_MAINNET:
            network = DogecoinBTCMainNet
        if self.wallet.network == wallet_pb2.DOGECOIN_TESTNET:
            network = DogecoinTestNet
        if self.wallet.network == wallet_pb2.DASH_MAINNET:
            network = DashMainNet
        if self.wallet.network == wallet_pb2.DASH_INVERTED_MAINNET:
            network = DashInvertedMainNet
        if self.wallet.network == wallet_pb2.DASH_BTC_MAINNET:
            network = DashBTCMainNet
        if self.wallet.network == wallet_pb2.DASH_TESTNET:
            network = DashTestNet
        if self.wallet.network == wallet_pb2.DASH_INVERTED_TESTNET:
            network = DashInvertedTestNet
        if self.wallet.network == wallet_pb2.BITCOIN_CASH_MAINNET:
            network = BitcoinCashMainNet
        if self.wallet.network == wallet_pb2.BLOCKCYPHER_TESTNET:
            network = BlockcypherTestNet
        else:
            raise ValueError("Unkown network")


    def get_transaction_history(self, max_cycles=100):
        addresses = [a.address for a in self.wallet.addresses]

        fullnode_endpoints = []
        esplora_endpoints = []
        blockcypher_tokens = []
        
        for node_pb2 in self.wallet.fullnode_endpoints:
            node = {}
            if node_pb2.url:
                node['url'] = node_pb2.url
            if node_pb2.user:
                node['user'] = node_pb2.user
            if node_pb2.password:
                node['password'] = node_pb2.password
            fullnode_endpoints.append(node)
        
        for node_pb2 in self.wallet.esplora_endpoints:
            node = {}
            if node_pb2.url:
                node['url'] = node_pb2.url
            esplora_endpoints.append(node)
                    
        for token in self.wallet.blockcypher_tokens:
            blockcypher_tokens.append(token)

        kwargs = {'fullnode_endpoints': fullnode_endpoints, 'esplora_endpoints': esplora_endpoints, 'blockcypher_tokens': blockcypher_tokens}

        if self.network.COIN == "BCY":
            address_client = BCYAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "BTC" and not self.network.TESTNET:
            address_client = BitcoinAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "BTC" and self.network.TESTNET:
            address_client = BitcoinTestAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "LTC" and not self.network.TESTNET:
            address_client = LitecoinAddress( addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "DOGE" and not self.network.TESTNET:
            address_client = DogecoinAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "DASH" and not self.network.TESTNET:
            address_client = DashAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        elif self.network.COIN == "ETH" and not self.network.TESTNET:
            address_client = EthereumAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
        else:
            raise ValueError("No address client for this network")

        address_client.sync()
        transactions = address_client.get_transaction_history()
        self.wallet.transactions = transactions
        tx_array = []
        for t in transactions:
            tx_array.append(Transaction(t, self.network))
        return tx_array
    
    def get_utxos(self, max_cycles=100):
        addresses = [a.address for a in self.wallet.addresses]

        transactions = self.get_transaction_history(max_cycles=max_cycles)
        utxo_set = []
        for t in transactions:
            for i in range(len(t.outputs())):
                try:
                    utxo_set.append(UTXO(t, i, addresses, only_mine=True))
                except ValueError:
                    pass
        return utxo_set
    
    def get_balance(self, in_standard_units=True, max_cycles=100):
        addresses = [a.address for a in self.wallet.addresses]
        
        if self.network.SUPPORTS_EVM:
            # We must use the Web3 network to get the balance as UTXOs are not available and getting transaction history
            # of an address is impractically slow.
            fullnode_endpoints = []
            
            for node_pb2 in self.wallet.fullnode_endpoints:
                node = {}
                if node_pb2.url:
                    node['url'] = node_pb2.url
                if node_pb2.user:
                    node['user'] = node_pb2.user
                if node_pb2.password:
                    node['password'] = node_pb2.password
                fullnode_endpoints.append(node)
            kwargs = {'fullnode_endpoints': fullnode_endpoints}
            address_client = EthereumAddress(addresses, transactions=self.wallet.transactions, max_cycles=max_cycles, **kwargs)
            balance = address_client.get_balance()
            if in_standard_units:
                return balance[0] / 1e18, balance[1] / 1e18
            else:
                return balance
        
        # Not an EVM chain

        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for u in utxos:
            total_balance = u.amount()
            if u.confirmed():
                confirmed_balance = u.amount()
        if in_standard_units:
            total_balance /= 1e8
            confirmed_balance /= 1e8
        return total_balance, confirmed_balance

    def addresses(self):
        return [a.address for a in self.wallet.addresses]
    
    def random_address(self):
        addresses = self.addresses()
        return addresses[randrange(0, len(addresses))]

    # Fee rate is in the unit used by the network, ie. vbytes, bytes or wei
    def create_transaction(self, password: bytes, destinations: List[Destination], fee_rate, spend_unconfirmed_inputs=False, **kwargs):
        inputs = self.get_utxos()
        
        private_keys = []
        for p in self.encrypted_private_keys:
            try:
                private_keys.append(decrypt(p, password))
            except PermissionError as e:
                del(private_keys)
                raise e

        if not spend_unconfirmed_inputs:
            _inputs = []
            for i in inputs:
                if i.confirmed():
                    _inputs.append(i)
            inputs = _inputs

        for ii in inputs:
            u = inputs[ii]
            for i in range (len(private_keys)):
                private_key = private_keys[i]
                privkey = PrivateKey.from_wif(private_key, self._network)
                a = [privkey.public_key.base58_address(True),
                     privkey.public_key.base58_address(False),
                     privkey.public_key.bech32_address()]
                u._output['private_key'] = private_key if u._output['address'] in a else None
                if u._output['address'] == a[0]:
                    u._output['script_pubkey'] = privkey.public_key.p2pkh_script(True)
                elif u._output['address'] == a[1]:
                    u._output['script_pubkey'] = privkey.public_key.p2pkh_script(False)
                if u._output['address'] == a[2]:
                    u._output['script_pubkey'] = privkey.public_key.p2wpkh_script()
                del(privkey)
                del(private_key)
                inputs[ii] = u

        fullnode_endpoints = []
        for f in self.wallet.fullnode_endpoints:
            _f = {}
            _f['url'] = f.url
            fullnode_endpoints.append(_f)

        if self._network.SUPPORTS_EVM:
            kwargs['gas'] = fee_rate
            create_transaction(inputs, destinations, network=self._network, full_nodes=fullnode_endpoints, **kwargs)
        
        # Depending on the size of the transactions, we may need to add a change output. Otherwise,
        # the remaining balance is going to the miner.
        # This is not the real change input, we need to find the size of the transaction first.
        change = Destination(self._network, self.random_address(), 0)
        inputs_without_change = inputs
        inputs_without_change.append(change)

        temp_transaction = create_transaction(inputs_without_change, destinations, network=self._network, full_nodes=fullnode_endpoints, **kwargs)
        size = transaction_size_simple(temp_transaction)
        total_inputs = sum([i.amount() for i in inputs])
        total_outputs = sum([o.amount() for o in destinations])
        if total_inputs > total_outputs + size*fee_rate:
            raise ValueError("Not enough balance for this transaction")
        change = Destination(self._network, self.random_address(), total_inputs - total_outputs - size*fee_rate)
        inputs.append(change)
        return create_transaction(inputs, destinations, network=self._network, full_nodes=fullnode_endpoints, **kwargs)


    def broadcast_transaction(self, transaction: bytes):
        broadcast_transaction(transaction, self._network)

    def serialze(self):
        return self.wallet.SerializeToString()