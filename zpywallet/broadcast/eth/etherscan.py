import asyncio

import requests
from ...errors import NetworkException
from ._helpers import extract_provider_error, extract_provider_txid, tx_hash_eth


async def broadcast_transaction_eth_etherscan(raw_transaction_hex, **kwargs):
    """Broadcast an Ethereum transaction using Etherscan.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
        api_key (str):
    """

    api_key = kwargs["api_key"]

    api_url = "https://api.etherscan.io/api"
    payload = {
        "module": "proxy",
        "action": "eth_sendRawTransaction",
        "hex": raw_transaction_hex,
        "apikey": api_key,
    }

    def _broadcast():
        try:
            response = requests.get(api_url, params=payload, timeout=30)
        except Exception as e:
            raise NetworkException(
                "Connection error while broadcasting transaction: {}".format(str(e))
            )

        try:
            result = response.json()
        except ValueError:
            result = None

        if response.status_code >= 300:
            message = extract_provider_error(result) or response.text
            raise NetworkException(
                "Failed to broadcast Ethereum transaction using Etherscan: "
                f"{message}"
            )

        error = extract_provider_error(result)
        if error is not None:
            raise NetworkException(
                "Failed to broadcast Ethereum transaction using Etherscan: "
                f"{error}"
            )

        return extract_provider_txid(result) or tx_hash_eth(raw_transaction_hex)

    return await asyncio.to_thread(_broadcast)
