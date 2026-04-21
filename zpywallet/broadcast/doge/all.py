import asyncio
from .blockcypher import broadcast_transaction_doge_blockcypher
from .dogechain import broadcast_transaction_doge_dogechain
from .fullnode import broadcast_transaction_doge_full_node
from ...nodes.doge import doge_nodes
from .._parallel import gather_broadcast_tasks
from .._tx_hash import tx_hash_bitcoin_like


def tx_hash_doge(raw_transaction_hex):
    """Calculate the hash of a Dogecoin transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return tx_hash_bitcoin_like(raw_transaction_hex)


async def broadcast_transaction_doge(raw_transaction_hex, **kwargs):
    """Broadcast a Dogecoin transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    awaitables = [
        broadcast_transaction_doge_blockcypher(raw_transaction_hex),
        broadcast_transaction_doge_dogechain(raw_transaction_hex),
    ]
    for node in rpc_nodes:
        awaitables.append(broadcast_transaction_doge_full_node(raw_transaction_hex, **node))
    for node in doge_nodes:
        awaitables.append(broadcast_transaction_doge_full_node(raw_transaction_hex, **node))

    return await gather_broadcast_tasks(awaitables)
