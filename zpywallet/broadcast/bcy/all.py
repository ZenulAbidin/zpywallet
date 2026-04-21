import asyncio
from .blockcypher import broadcast_transaction_bcy_blockcypher
from .._parallel import gather_broadcast_tasks
from .._tx_hash import tx_hash_bitcoin_like


def tx_hash_bcy(raw_transaction_hex):
    """Calculate the hash of a Blockcypher testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """
    return tx_hash_bitcoin_like(raw_transaction_hex)


async def broadcast_transaction_bcy(raw_transaction_hex):
    """Broadcast a Blockcypher testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    awaitables = [broadcast_transaction_bcy_blockcypher(raw_transaction_hex)]
    return await gather_broadcast_tasks(awaitables)
