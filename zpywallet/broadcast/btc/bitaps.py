import requests

from ...errors import NetworkException
from .._provider_success import bitcoin_like_broadcast_success_txid


async def broadcast_transaction_btc_bitaps(raw_transaction_hex):
    """Broadcast a Bitcoin transaction using Bitaps.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://api.bitaps.com/btc/v1/create/tx/push"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            "Failed to broadcast transaction using Bitaps API: {}".format(response.text)
        )

    return bitcoin_like_broadcast_success_txid(raw_transaction_hex)
