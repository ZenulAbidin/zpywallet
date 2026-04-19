import asyncio
import binascii
import hashlib
from .fullnode import broadcast_transaction_dashtest_full_node
from .._parallel import gather_broadcast_tasks


def tx_hash_dashtest(raw_transaction_hex):
    """Calculate the hash of a Dash testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_dashtest(raw_transaction_hex, **kwargs):
    """Broadcast a Dash testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    awaitables = []
    for node in rpc_nodes:
        awaitables.append(
            broadcast_transaction_dashtest_full_node(raw_transaction_hex, **node)
        )

    await gather_broadcast_tasks(awaitables)
