import requests

from ...errors import NetworkException


async def broadcast_transaction_btc_mempool_space(raw_transaction_hex):
    """Broadcast a Bitcoin transaction using Mempool.space.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://mempool.space/api/tx"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
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
