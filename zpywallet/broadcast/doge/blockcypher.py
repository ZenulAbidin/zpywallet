import requests

from ...errors import NetworkException

async def broadcast_transaction_doge_blockcypher(raw_transaction_hex):
    api_url = "https://api.blockcypher.com/v1/doge/main/txs/push"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast Dogecoin transaction using BlockCypher API: {}".format(response.text))