import asyncio
from .bitaps import broadcast_transaction_btctest_bitaps
from .blockchair import broadcast_transaction_btctest_blockchair
from .blockcypher import broadcast_transaction_btctest_blockcypher
from .blockstream import broadcast_transaction_btctest_blockstream
from .esplora import broadcast_transaction_btctest_esplora
from .fullnode import broadcast_transaction_btctest_full_node
from .mempool_space import broadcast_transaction_btctest_mempool_space
from ...nodes.btctest import btctest_nodes, btctest_esplora_nodes
from .._parallel import gather_broadcast_tasks
from .._tx_hash import tx_hash_bitcoin_like


def tx_hash_btctest(raw_transaction_hex):
    """Calculate the hash of a Bitcoin testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return tx_hash_bitcoin_like(raw_transaction_hex)


async def broadcast_transaction_btctest(raw_transaction_hex, **kwargs):
    """Broadcast a Bitcoin testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []
    esplora_nodes = kwargs.get("esplora_nodes") or []

    awaitables = [
        broadcast_transaction_btctest_bitaps(raw_transaction_hex),
        broadcast_transaction_btctest_blockchair(raw_transaction_hex),
        broadcast_transaction_btctest_blockcypher(raw_transaction_hex),
        broadcast_transaction_btctest_blockstream(raw_transaction_hex),
        broadcast_transaction_btctest_mempool_space(raw_transaction_hex),
    ]
    for node in rpc_nodes:
        awaitables.append(
            broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)
        )
    for node in btctest_nodes:
        awaitables.append(
            broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)
        )
    for node in esplora_nodes:
        awaitables.append(
            broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)
        )
    for node in btctest_esplora_nodes:
        awaitables.append(
            broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)
        )

    return await gather_broadcast_tasks(awaitables)
