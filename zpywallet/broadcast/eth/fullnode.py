from web3 import Web3
from ...errors import NetworkException


async def broadcast_transaction_eth_generic(raw_transaction_hex, **kwargs):
    """Broadcast an Ethereum transaction using a full node.
    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
        url (str): The Web3 URL of the node. Include the port if necessary.
    """

    if isinstance(raw_transaction_hex, str):
        normalized = (
            raw_transaction_hex[2:]
            if raw_transaction_hex.startswith("0x")
            else raw_transaction_hex
        )
        raw_transaction_hex = bytes.fromhex(normalized)

    try:
        w3 = Web3(Web3.HTTPProvider(kwargs.get("url")))
        send_raw_transaction = getattr(w3.eth, "send_raw_transaction", None)
        if send_raw_transaction is None:
            send_raw_transaction = w3.eth.sendRawTransaction
        transaction_hash = send_raw_transaction(raw_transaction_hex)
        return transaction_hash.hex()
    except Exception as e:
        raise NetworkException(
            f"Failed to broadcast Ethereum transaction using generic provider: {e}"
        )
