import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_ltc_blockchair(raw_transaction_hex):
    api_url = "https://api.blockchair.com/litecoin/push/transaction"
    payload = {"data": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload)
    except ConnectionError as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast Litecoin transaction using Blockchair API: {}".format(response.text))
