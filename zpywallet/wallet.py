# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

import json
import math
from os import urandom
from Cryptodome import Random
from typing import List

from zpywallet.utxo import UTXO

from .destination import Destination, FeePolicy

from .mnemonic import Mnemonic
from .utils.bip32 import HDWallet

from .utils.keys import PrivateKey, PublicKey
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
    BlockcypherTestNet,
)

from .address import CryptoClient

from .nodes.eth import eth_nodes

from .utils.aes import encrypt_str, decrypt_str

from .transaction import Transaction


def generate_mnemonic(strength=128):
    """Creates a new seed phrase of the specified length"""
    if strength % 32 != 0:
        raise ValueError("strength must be a multiple of 32")
    if strength < 128 or strength > 256:
        raise ValueError("strength should be >= 128 and <= 256")
    entropy = urandom(strength // 8)
    mne = Mnemonic(language="english")
    mnemonic = mne.to_mnemonic(entropy)
    return mnemonic


def create_wallet(
    mnemonic=None, network=BitcoinSegwitMainNet, strength=128
) -> HDWallet:
    """Deprecated: This function will be removed in v1.0

    Generate a new wallet class from a mnemonic phrase, optionally
    randomly generated

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

    def __init__(
        self,
        network,
        seed_phrase,
        password,
        receive_gap_limit=1000,
        change_gap_limit=1000,
        derivation_path=None,
        _with_wallet=True,
        max_cycles=100,
        **kwargs,
    ):
        """
        Initializes a Wallet object.

        Args:
            network: The network associated with the wallet.
            seed_phrase: The seed phrase for the wallet.
            password: The password to encrypt the wallet.
            receive_gap_limit (int, optional): The maximum gap limit for receive addresses. Defaults to 1000.
            change_gap_limit (int, optional): The maximum gap limit for change addresses. Defaults to 1000.
            derivation_path (str, optional): The derivation path for the wallet. Defaults to None.
            max_cycles (int, optional): The maximum number of cycles. Defaults to 100.
            fullnode_endpoints (list, optional): List of full node endpoints. Defaults to None.
            esplora_endpoints (list, optional): List of Esplora endpoints. Defaults to None.
            blockcypher_tokens (list, optional): List of Blockcypher tokens. Defaults to None.

        Raises:
            ValueError: If an unknown network is provided or if the derivation path is invalid.
        """

        fullnode_endpoints = kwargs.get("fullnode_endpoints")
        esplora_endpoints = kwargs.get("esplora_endpoints")
        blockcypher_tokens = kwargs.get("blockcypher_tokens")

        self._network = network
        derivation_path = derivation_path or (
            network.BIP32_SEGWIT_PATH or network.BIP32_PATH
        )

        seed_phrase = seed_phrase or generate_mnemonic()

        if not _with_wallet:
            return

        self.container = wallet_pb2.Wallet()
        self.container.SerializeToString()
        self.container.receive_gap_limit = receive_gap_limit
        self.container.change_gap_limit = change_gap_limit
        self.container.height = 0

        self.container.derivation_path = derivation_path
        if not isinstance(derivation_path, str):
            raise ValueError("Invalid derivation path")

        # Generate addresses and keys
        hdwallet = HDWallet.from_mnemonic(mnemonic=seed_phrase, network=network)

        # We do not save the password. Instead, we are going to
        # generate a base64-encrypted serialization of this wallet file
        # using the password.
        self.container.encrypted_seed_phrase = encrypt_str(
            seed_phrase, password
        )  # AES-256-SIV encryption

        # Set properties
        network_map = {
            BitcoinSegwitMainNet: wallet_pb2.BITCOIN_SEGWIT_MAINNET,
            BitcoinMainNet: wallet_pb2.BITCOIN_MAINNET,
            BitcoinSegwitTestNet: wallet_pb2.BITCOIN_SEGWIT_TESTNET,
            BitcoinTestNet: wallet_pb2.BITCOIN_TESTNET,
            LitecoinSegwitMainNet: wallet_pb2.LITECOIN_SEGWIT_MAINNET,
            LitecoinMainNet: wallet_pb2.LITECOIN_MAINNET,
            LitecoinBTCSegwitMainNet: wallet_pb2.LITECOIN_BTC_SEGWIT_MAINNET,
            LitecoinBTCMainNet: wallet_pb2.LITECOIN_BTC_MAINNET,
            LitecoinSegwitTestNet: wallet_pb2.LITECOIN_SEGWIT_TESTNET,
            LitecoinTestNet: wallet_pb2.LITECOIN_TESTNET,
            EthereumMainNet: wallet_pb2.ETHEREUM_MAINNET,
            DogecoinMainNet: wallet_pb2.DOGECOIN_MAINNET,
            DogecoinBTCMainNet: wallet_pb2.DOGECOIN_BTC_MAINNET,
            DogecoinTestNet: wallet_pb2.DOGECOIN_TESTNET,
            DashMainNet: wallet_pb2.DASH_MAINNET,
            DashInvertedMainNet: wallet_pb2.DASH_INVERTED_MAINNET,
            DashBTCMainNet: wallet_pb2.DASH_BTC_MAINNET,
            DashTestNet: wallet_pb2.DASH_TESTNET,
            DashInvertedTestNet: wallet_pb2.DASH_INVERTED_TESTNET,
            BitcoinCashMainNet: wallet_pb2.BITCOIN_CASH_MAINNET,
            BlockcypherTestNet: wallet_pb2.BLOCKCYPHER_TESTNET,
        }

        self.container.network = network_map.get(network)
        if self.container.network is None:
            raise ValueError("Unknown network")

        self.container.fullnode_endpoints.extend(fullnode_endpoints or [])
        self.container.esplora_endpoints.extend(esplora_endpoints or [])
        self.container.blockcypher_tokens.extend(blockcypher_tokens or [])

        self.encrypted_private_keys = []
        for i in range(0, receive_gap_limit):
            privkey = hdwallet.get_child_for_path(
                f"{derivation_path}/0/{i}"
            ).private_key
            pubkey = privkey.public_key

            # Add an Address
            address = self.container.addresses.add()
            address.address = pubkey.address()
            address.pubkey = pubkey.to_hex()
            self.encrypted_private_keys.append(
                privkey.to_hex() if network.SUPPORTS_EVM else privkey.to_wif()
            )
        self.encrypted_private_keys = encrypt_str(
            json.dumps(self.encrypted_private_keys), password
        )

        self._setup_client(max_cycles=max_cycles)

    @classmethod
    def deserialize(cls, data: bytes, password, max_cycles=100):
        """
        Deserialize a Wallet object from its byte representation.

        Args:
            cls: The class object.
            data (bytes): The byte representation of the Wallet object.
            password: The password used to encrypt the wallet.
            max_cycles (int, optional): The maximum number of cycles. Defaults to 100.

        Returns:
            Wallet: The deserialized Wallet object.

        Raises:
            ValueError: If an unknown network is encountered during deserialization.
        """
        wallet = wallet_pb2.Wallet()
        wallet.ParseFromString(data)
        seed_phrase = decrypt_str(wallet.encrypted_seed_phrase, password)

        network_map = {
            wallet_pb2.BITCOIN_SEGWIT_MAINNET: BitcoinSegwitMainNet,
            wallet_pb2.BITCOIN_MAINNET: BitcoinMainNet,
            wallet_pb2.BITCOIN_SEGWIT_TESTNET: BitcoinSegwitTestNet,
            wallet_pb2.BITCOIN_TESTNET: BitcoinTestNet,
            wallet_pb2.LITECOIN_SEGWIT_MAINNET: LitecoinSegwitMainNet,
            wallet_pb2.LITECOIN_MAINNET: LitecoinMainNet,
            wallet_pb2.LITECOIN_BTC_SEGWIT_MAINNET: LitecoinBTCSegwitMainNet,
            wallet_pb2.LITECOIN_BTC_MAINNET: LitecoinBTCMainNet,
            wallet_pb2.LITECOIN_SEGWIT_TESTNET: LitecoinSegwitTestNet,
            wallet_pb2.LITECOIN_TESTNET: LitecoinTestNet,
            wallet_pb2.ETHEREUM_MAINNET: EthereumMainNet,
            wallet_pb2.DOGECOIN_MAINNET: DogecoinMainNet,
            wallet_pb2.DOGECOIN_BTC_MAINNET: DogecoinBTCMainNet,
            wallet_pb2.DOGECOIN_TESTNET: DogecoinTestNet,
            wallet_pb2.DASH_MAINNET: DashMainNet,
            wallet_pb2.DASH_INVERTED_MAINNET: DashInvertedMainNet,
            wallet_pb2.DASH_BTC_MAINNET: DashBTCMainNet,
            wallet_pb2.DASH_TESTNET: DashTestNet,
            wallet_pb2.DASH_INVERTED_TESTNET: DashInvertedTestNet,
            wallet_pb2.BITCOIN_CASH_MAINNET: BitcoinCashMainNet,
            wallet_pb2.BLOCKCYPHER_TESTNET: BlockcypherTestNet,
        }

        network = network_map.get(wallet.network)
        if network is None:
            raise ValueError("Unknown network")

        self = cls(network, seed_phrase, password, _with_wallet=False)
        self.container = wallet
        hdwallet = HDWallet.from_mnemonic(mnemonic=seed_phrase, network=network)

        self.encrypted_private_keys = []
        for i in range(0, self.container.receive_gap_limit):
            privkey = hdwallet.get_child_for_path(
                f"{self.container.derivation_path}/0/{i}"
            ).private_key
            self.encrypted_private_keys.append(
                privkey.to_hex() if network.SUPPORTS_EVM else privkey.to_wif()
            )
            pubkey = privkey.public_key

            # Add an Address
            address = self.container.addresses.add()
            address.address = pubkey.address()
            address.pubkey = pubkey.to_hex()
        self.encrypted_private_keys = encrypt_str(
            json.dumps(self.encrypted_private_keys), password
        )

        del seed_phrase
        del password

        self._setup_client(max_cycles=max_cycles)

    def network(self):
        """
        Get the network associated with the wallet.

        Returns:
            CryptoNetwork: The network associated with the wallet.
        """
        return self._network

    def _setup_client(self, max_cycles=100):
        addresses = [a.address for a in self.container.addresses]

        fullnode_endpoints = []
        esplora_endpoints = []
        blockcypher_tokens = []

        for node_pb2 in self.container.fullnode_endpoints:
            node = {}
            if node_pb2.url:
                node["url"] = node_pb2.url
            if node_pb2.user:
                node["user"] = node_pb2.user
            if node_pb2.password:
                node["password"] = node_pb2.password
            fullnode_endpoints.append(node)

        for node_pb2 in self.container.esplora_endpoints:
            node = {}
            if node_pb2.url:
                node["url"] = node_pb2.url
            esplora_endpoints.append(node)

        for token in self.container.blockcypher_tokens:
            blockcypher_tokens.append(token)

        kwargs = {
            "fullnode_endpoints": fullnode_endpoints,
            "esplora_endpoints": esplora_endpoints,
            "blockcypher_tokens": blockcypher_tokens,
        }

        self.client = CryptoClient(
            addresses,
            coin=self._network.COIN,
            chain="test" if self._network.TESTNET else "main",
            transactions=self.container.transactions,
            max_cycles=max_cycles,
            **kwargs,
        )

    def get_transaction_history(self):
        """
        Get the transaction history associated with the wallet.

        Returns:
            List[Transaction]: The list of transactions in the wallet's history.
        """
        transactions = self.client.get_transaction_history()
        # Create a set to keep track of unique txid values
        seen_txids = set()

        # List to store deduplicated transactions
        deduplicated_transactions = []

        # Iterate through transactions
        for transaction in transactions:
            txid = transaction.txid

            # Check if txid is not seen before
            if txid not in seen_txids:
                # Add the transaction to the deduplicated list
                deduplicated_transactions.append(transaction)

                # Mark this txid as seen
                seen_txids.add(txid)

        # Update the transactions list with deduplicated transactions
        transactions = deduplicated_transactions
        del self.container.transactions[:]
        self.container.transactions.extend(transactions)
        tx_array = []
        for t in transactions:
            tx_array.append(Transaction(t, self._network))
        return tx_array

    def get_utxos(self, only_unspent=False):
        """
        Get the unspent transaction outputs (UTXOs) associated with the wallet.

        Args:
            only_unspent (bool, optional): If True, only unspent UTXOs are retrieved. Defaults to False.

        Returns:
            List[UTXO]: The list of unspent transaction outputs.
        """
        addresses = [a.address for a in self.container.addresses]

        transactions = self.get_transaction_history()
        utxo_set = []
        for t in transactions:
            for i in range(len(t.sat_outputs(only_unspent=only_unspent))):
                try:
                    utxo_set.append(
                        UTXO(
                            t,
                            i,
                            addresses=addresses,
                            other_transactions=transactions,
                            only_mine=True,
                        )
                    )
                except ValueError:
                    pass

        return utxo_set

    def _to_human_friendly_utxo(self, inputs, private_keys):
        new_inputs = []
        for ii in range(len(inputs)):
            u = inputs[ii]
            for i in range(len(private_keys)):
                private_key = private_keys[i]
                privkey = PrivateKey.from_wif(private_key.decode(), self._network)
                try:
                    a = [
                        privkey.public_key.base58_address(True),
                        privkey.public_key.base58_address(False),
                        privkey.public_key.bech32_address(),
                    ]
                except Exception:
                    a = [
                        privkey.public_key.base58_address(True),
                        privkey.public_key.base58_address(False),
                    ]
                u._output["private_key"] = (
                    privkey if u._output["address"] in a else None
                )
                u._output["address_hash"] = privkey.public_key.hash160()
                del private_key
                if u._output["private_key"] is None:
                    continue
                new_inputs.append(u)
                break
        return new_inputs

    def get_balance(self, in_standard_units=True):
        """
        Get the balance of the wallet.

        Args:
            in_standard_units (bool, optional): If True, balance is returned in standard units (e.g., BTC, ETH).
                If False, balance is returned in raw units (e.g., satoshi, wei). Defaults to True.

        Returns:
            Tuple[float, float]: The total balance and confirmed balance of the wallet.
        """
        if self._network.SUPPORTS_EVM:
            # We must use the Web3 network to get the balance as UTXOs are not
            # available and getting transaction history of an address is
            # impractically slow.
            balance = self.client.get_balance()
            if in_standard_units:
                return balance[0] / 1e18, balance[1] / 1e18
            else:
                return balance

        # Not an EVM chain

        total_balance = 0
        confirmed_balance = 0

        utxos = self.get_utxos(only_unspent=True)
        for u in utxos:
            confirmed_balance += u.amount(in_standard_units=in_standard_units)

        utxos = self.get_utxos()
        for u in utxos:
            total_balance += u.amount(in_standard_units=in_standard_units)

        return total_balance, confirmed_balance

    def addresses(self):
        """
        Get the addresses associated with the wallet.

        Returns:
            List[str]: The list of addresses associated with the wallet.
        """
        return [a.address for a in self.container.addresses]

    def random_address(self):
        """
        Get a random address from the wallet.

        Returns:
            str: A randomly selected address from the wallet.
        """
        addresses = self.addresses()

        # Use a secure RNG to resist blockchain analysis
        limit = len(addresses)

        # Convert bits to bytes and round up to the nearest byte
        watermark = int(math.ceil(math.log2(len(addresses)))) // 8

        while limit >= len(addresses):
            limit = int.from_bytes(Random.new().read(watermark), byteorder="big")
        return addresses[limit]

    def private_keys(self, password):
        """
        Get the private keys associated with the wallet.

        Args:
            password: The password used to encrypt the wallet.

        Returns:
            List[str]: The list of private keys associated with the wallet.
        """
        private_keys = []
        try:
            private_keys = json.loads(
                decrypt_str(self.encrypted_private_keys, password)
            )
            return private_keys
        except ValueError as e:
            del private_keys
            raise e

    def _add_stock_nodes(self):
        fullnode_endpoints = []
        for f in self.container.fullnode_endpoints:
            _f = {}
            _f["url"] = f.url
            fullnode_endpoints.append(_f)
        if not self._network.SUPPORTS_EVM:
            return fullnode_endpoints
        else:
            if self._network.COIN == "ETH":
                fullnode_endpoints.extend(eth_nodes)
            return fullnode_endpoints

    def _calculate_change(self, inputs, destinations, fee_rate):
        temp_transaction = create_transaction(
            inputs, destinations, network=self._network
        )
        size = transaction_size_simple(temp_transaction)
        total_inputs = sum([i.amount(in_standard_units=False) for i in inputs])
        total_outputs = sum([o.amount(in_standard_units=False) for o in destinations])
        fee_proportional_outputs = [
            o for o in destinations if o.fee_policy() == FeePolicy.PROPORTIONAL
        ]

        if total_inputs < total_outputs + size * fee_rate:
            if fee_proportional_outputs:
                proportional_fee = int(
                    math.ceil((size * fee_rate) / len(fee_proportional_outputs))
                )
                old_destinations = destinations
                destinations = []
                for o in old_destinations:
                    if o.fee_policy() == FeePolicy.PROPORTIONAL:
                        o._amount -= proportional_fee
                    destinations.append(o)
            else:
                raise ValueError("Not enough balance for this transaction")

        # If after applying proportional fee scaling we STILL don't have
        # enough balance, then that means the outputs are greater than the
        # inputs (possibly a dust input set). In this case, the total_outputs
        # is most likely negative.
        total_outputs = sum([o.amount(in_standard_units=False) for o in destinations])
        if total_inputs < total_outputs + size * fee_rate:
            raise ValueError(
                "Not enough balance for this transaction "
                "(are you trying to send dust amounts?)"
            )

        change = total_inputs - total_outputs - size * fee_rate
        return (
            None
            if change <= 0
            else Destination(self.random_address(), change / 1e8, self._network)
        )

    # Fee rate is in the unit used by the network, ie. vbytes, bytes or wei
    def create_transaction(
        self,
        password: bytes,
        destinations: List[Destination],
        fee_rate=None,
        spend_unconfirmed_inputs=False,
        **kwargs,
    ):
        """
        Create a transaction.

        Args:
            password (bytes): The password used to encrypt the wallet.
            destinations (List[Destination]): The list of destinations for the transaction.
            fee_rate: The fee rate for the transaction.
            spend_unconfirmed_inputs (bool, optional): If True, spend unconfirmed inputs. Defaults to False.

        Returns:
            Transaction: The created transaction.
        """
        inputs = self.get_utxos(only_unspent=True)

        if not spend_unconfirmed_inputs:
            confirmed_inputs = []
            for i in inputs:
                if i.height():
                    confirmed_inputs.append(i)
            inputs = confirmed_inputs

        private_keys = self.private_keys(password)

        inputs = self._to_human_friendly_utxo(inputs, private_keys)

        fullnode_endpoints = self._add_stock_nodes()

        if self._network.SUPPORTS_EVM:
            # Note: On EVM chains we do NOT need to estimate the fee.
            # Web3.py does all the heavy lifting for us.
            create_transaction(
                inputs,
                destinations,
                network=self._network,
                full_nodes=fullnode_endpoints,
                **kwargs,
            )

        # Depending on the size of the transactions, we may need to add a
        # change output. Otherwise, the remaining balance is going to the miner.
        # This is not the real change input, we need to find the size of the
        # transaction first.
        change = Destination(self.random_address(), 0, self._network)
        destinations_without_change = destinations[:]
        destinations_without_change.append(change)

        change = self._calculate_change(inputs, destinations_without_change, fee_rate)
        if change:
            destinations.append(change)
        return create_transaction(inputs, destinations, network=self._network)

    def broadcast_transaction(self, transaction):
        """
        Broadcast a transaction to the network.

        Args:
            transaction: The transaction to broadcast.
        """
        broadcast_transaction(transaction, self._network)

    def serialize(self):
        """
        Serialize the wallet object.

        Returns:
            bytes: The serialized representation of the wallet.
        """
        return self.container.SerializeToString()
