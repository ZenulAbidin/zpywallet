import asyncio

import requests
from ...errors import NetworkException


async def broadcast_transaction_eth_mew(raw_transaction_hex):
    """Broadcast an Ethereum testnet transaction using MyEtherWallet (MEW).

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    def _broadcast():
        api_url = "https://api.mewapi.io/v1/transaction/sendRaw"
        payload = {
            "rawTx": raw_transaction_hex,
        }

        try:
            response = requests.post(api_url, json=payload, timeout=30)
        except Exception as e:
            raise NetworkException(
                "Connection error while broadcasting transaction: {}".format(str(e))
            )

        result = response.json()
        if response.status_code >= 300 and result.get("status") == "1":
            raise NetworkException(
                "Failed to broadcast Ethereum transaction using MyEtherWallet: "
                f"{result.get('message')}"
            )

    return await asyncio.to_thread(_broadcast)
