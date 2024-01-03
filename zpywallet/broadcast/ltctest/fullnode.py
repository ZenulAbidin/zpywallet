import requests
from ...errors import NetworkException

def broadcast_transaction_ltctest_full_node(raw_transaction_hex, rpc_user, rpc_password, rpc_host, rpc_port):
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "sendrawtransaction",
        "params": [raw_transaction_hex],
    }

    response = requests.post(rpc_url, json=payload)
    result = response.json()

    if "error" in result:
        raise NetworkException(f"Failed to broadcast Litecoin testnet transaction using full node: {result['error']}")
    
    return result["result"]
