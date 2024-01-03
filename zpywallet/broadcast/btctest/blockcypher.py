import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btctest_blockcypher(raw_transaction_hex):
    api_url = "https://api.blockcypher.com/v1/btc/test3/txs/push"
    payload = {"tx": raw_transaction_hex}

    response = requests.post(api_url, json=payload)

    if response.status_code == 201:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast testnet transaction using Blockcypher API: {}".format(response.text))
