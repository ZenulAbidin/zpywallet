import requests
from ...errors import NetworkException

def broadcast_transaction_eth_etherscan(raw_transaction_hex, api_key):
    api_url = f"https://api.etherscan.io/api"
    payload = {
        "module": "proxy",
        "action": "eth_sendRawTransaction",
        "hex": raw_transaction_hex,
        "apikey": api_key,
    }

    try:
        response = requests.get(api_url, params=payload)
    except ConnectionError as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))
    
    result = response.json()

    if result.get("status") == "1":
        return result.get("result")
    else:
        raise NetworkException(f"Failed to broadcast Ethereum transaction using Etherscan: {result.get('message')}")
