import requests

from ...errors import NetworkException
from .._provider_success import bitcoin_like_broadcast_success_txid


async def broadcast_transaction_btc_mempool_space(raw_transaction_hex):
    """Broadcast a Bitcoin transaction using Mempool.space.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://mempool.space/api/tx"
    headers = {"Content-Type": "text/plain"}

    try:
        response = requests.post(
            api_url, data=raw_transaction_hex, headers=headers, timeout=30
        )
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            "Failed to broadcast transaction using Mempool Space API: {}".format(
                response.text
            )
        )

    return bitcoin_like_broadcast_success_txid(raw_transaction_hex)
