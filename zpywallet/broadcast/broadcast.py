import asyncio
from .bcy.all import broadcast_transaction_bcy, tx_hash_bcy
from .btc.all import broadcast_transaction_btc, tx_hash_btc
from .btctest.all import broadcast_transaction_btctest, tx_hash_btctest
from .dash.all import broadcast_transaction_dash, tx_hash_dash
from .dashtest.all import broadcast_transaction_dashtest, tx_hash_dashtest
from .doge.all import broadcast_transaction_doge, tx_hash_doge
from .dogetest.all import broadcast_transaction_dogetest, tx_hash_dogetest
from .eth.all import broadcast_transaction_eth, tx_hash_eth
from .ltc.all import broadcast_transaction_ltc, tx_hash_ltc
from .ltctest.all import broadcast_transaction_ltctest, tx_hash_ltctest


def broadcast_transaction(transaction, network, **kwargs):
    if network.COIN == "BTC":
        if not network.TESTNET:
            return asyncio.run(broadcast_transaction_btc(transaction, **kwargs))
        else:
            return asyncio.run(broadcast_transaction_btctest(transaction, **kwargs))
    elif network.COIN == "LTC":
        if not network.TESTNET:
            return asyncio.run(broadcast_transaction_ltc(transaction, **kwargs))
        else:
            return asyncio.run(broadcast_transaction_ltctest(transaction, **kwargs))
    elif network.COIN == "DASH":
        if not network.TESTNET:
            return asyncio.run(broadcast_transaction_dash(transaction, **kwargs))
        else:
            return asyncio.run(broadcast_transaction_dashtest(transaction, **kwargs))
    elif network.COIN == "DOGE":
        if not network.TESTNET:
            return asyncio.run(broadcast_transaction_doge(transaction, **kwargs))
        else:
            return asyncio.run(broadcast_transaction_dogetest(transaction, **kwargs))
    elif network.COIN == "ETH":
        return asyncio.run(
            broadcast_transaction_eth(transaction, network=network, **kwargs)
        )
    elif network.COIN == "BCY":
        return asyncio.run(broadcast_transaction_bcy(transaction, **kwargs))
    else:
        raise ValueError("Cannot broadcast transaction: Unsupported network")


def tx_hash(transaction: bytes, network):
    if network.COIN == "BTC":
        if not network.TESTNET:
            return tx_hash_btc(transaction)
        else:
            return tx_hash_btctest(transaction)
    elif network.COIN == "LTC":
        if not network.TESTNET:
            return tx_hash_ltc(transaction)
        else:
            return tx_hash_ltctest(transaction)
    elif network.COIN == "DASH":
        if not network.TESTNET:
            return tx_hash_dash(transaction)
        else:
            return tx_hash_dashtest(transaction)
    elif network.COIN == "DOGE":
        if not network.TESTNET:
            return tx_hash_doge(transaction)
        else:
            return tx_hash_dogetest(transaction)
    elif network.COIN == "ETH":
        return tx_hash_eth(transaction)
    elif network.COIN == "BCY":
        return tx_hash_bcy(transaction)
    else:
        raise ValueError("Cannot broadcast transaction: Unsupported network")
