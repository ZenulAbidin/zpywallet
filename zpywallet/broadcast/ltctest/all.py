import asyncio
from .blockchair import broadcast_transaction_ltctest_blockchair
from .blockcypher import broadcast_transaction_ltctest_blockcypher
from .fullnode import broadcast_transaction_ltctest_full_node
from .._parallel import gather_broadcast_tasks
from .._tx_hash import tx_hash_bitcoin_like


def tx_hash_ltctest(raw_transaction_hex):
    """Calculate the hash of a Litecoin testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return tx_hash_bitcoin_like(raw_transaction_hex)


async def broadcast_transaction_ltctest(raw_transaction_hex, **kwargs):
    """Broadcast a Litecoin testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    awaitables = [
        broadcast_transaction_ltctest_blockchair(raw_transaction_hex),
        broadcast_transaction_ltctest_blockcypher(raw_transaction_hex),
    ]
    for node in rpc_nodes:
        awaitables.append(
            broadcast_transaction_ltctest_full_node(raw_transaction_hex, **node)
        )

    return await gather_broadcast_tasks(awaitables)
