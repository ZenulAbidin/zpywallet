import asyncio
import binascii
from .blockcypher import broadcast_transaction_eth_blockcypher
from .fullnode import broadcast_transaction_eth_generic
from .mew import broadcast_transaction_eth_mew
from ...nodes.eth import eth_nodes
from ...utils.keccak import Keccak256


def _extract_raw_transaction(raw_transaction_hex):
    if isinstance(raw_transaction_hex, dict):
        for key in ("raw_transaction", "rawTransaction"):
            if key in raw_transaction_hex:
                return _extract_raw_transaction(raw_transaction_hex[key])

    for attr in ("raw_transaction", "rawTransaction"):
        if hasattr(raw_transaction_hex, attr):
            return _extract_raw_transaction(getattr(raw_transaction_hex, attr))

    return raw_transaction_hex


def _normalize_raw_transaction(raw_transaction_hex):
    raw_transaction_hex = _extract_raw_transaction(raw_transaction_hex)

    if isinstance(raw_transaction_hex, (bytes, bytearray)):
        raw_bytes = bytes(raw_transaction_hex)
        if raw_bytes.startswith(b"0x"):
            try:
                return bytes.fromhex(raw_bytes[2:].decode()).hex()
            except ValueError:
                pass

        try:
            decoded = raw_bytes.decode()
        except UnicodeDecodeError:
            return raw_bytes.hex()

        raw_transaction_hex = decoded

    if not isinstance(raw_transaction_hex, str):
        raise TypeError("Unsupported Ethereum transaction payload")

    normalized = (
        raw_transaction_hex[2:]
        if raw_transaction_hex.startswith("0x")
        else raw_transaction_hex
    )
    try:
        bytes.fromhex(normalized)
    except ValueError:
        normalized = raw_transaction_hex.encode().hex()
    return normalized


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

    normalized_transaction = _normalize_raw_transaction(raw_transaction_hex)
    rpc_nodes = kwargs.get("rpc_nodes") or kwargs.get("fullnode_endpoints") or []

    awaitables = [
        broadcast_transaction_eth_blockcypher(normalized_transaction),
        broadcast_transaction_eth_mew(normalized_transaction),
    ]
    for node in rpc_nodes:
        awaitables.append(
            broadcast_transaction_eth_generic(normalized_transaction, **node)
        )
    for node in eth_nodes:
        awaitables.append(
            broadcast_transaction_eth_generic(normalized_transaction, **node)
        )

    await asyncio.gather(*awaitables, return_exceptions=True)
