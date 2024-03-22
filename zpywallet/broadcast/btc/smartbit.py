import requests

from ...errors import NetworkException


async def broadcast_transaction_btc_smartbit(raw_transaction_hex):
    """Broadcast a Bitcoin transaction using Smartbit.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://api.smartbit.com.au/v1/blockchain/pushtx"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload, timeout=30)
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            "Failed to broadcast transaction using Smartbit API: {}".format(
                response.text
            )
        )
