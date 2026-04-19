import asyncio
import binascii
from .blockcypher import broadcast_transaction_eth_blockcypher
from .fullnode import broadcast_transaction_eth_generic
from .mew import broadcast_transaction_eth_mew
from ...nodes.eth import eth_nodes
from ...utils.keccak import Keccak256


def _normalize_raw_transaction(raw_transaction_hex):
    if isinstance(raw_transaction_hex, bytes):
        raw_transaction_hex = raw_transaction_hex.decode()
    return (
        raw_transaction_hex[2:]
        if isinstance(raw_transaction_hex, str) and raw_transaction_hex.startswith("0x")
        else raw_transaction_hex
    )


def tx_hash_eth(raw_transaction_hex):
    """Calculate the hash of an Ethereum transaction.

    This function can also be used to calculate the hash of any kind of EVM token.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    normalized = _normalize_raw_transaction(raw_transaction_hex)
    return "0x" + Keccak256(bytes.fromhex(normalized)).hexdigest()


async def broadcast_transaction_eth(raw_transaction_hex, **kwargs):
    """Broadcast a Ethereum transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    It can also be used to broadcast the transaction of any kind of EVM token.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or kwargs.get("fullnode_endpoints") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_eth_blockcypher(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_eth_mew(raw_transaction_hex))
    )
    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_eth_generic(raw_transaction_hex, **node)
            )
        )
    for node in eth_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_eth_generic(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
