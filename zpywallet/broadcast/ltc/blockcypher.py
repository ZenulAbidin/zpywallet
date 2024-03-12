import requests

from ...errors import NetworkException


async def broadcast_transaction_ltc_blockcypher(raw_transaction_hex):
    """Broadcast a Litecoin transaction using Blockcypher.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://api.blockcypher.com/v1/ltc/main/txs/push"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            "Failed to broadcast Litecoin transaction using Blockcypher API: {}".format(
                response.text
            )
        )
