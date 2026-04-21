import asyncio

import requests
from ...errors import NetworkException
from ._helpers import extract_provider_error, extract_provider_txid, tx_hash_eth


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

        try:
            result = response.json()
        except ValueError:
            result = None

        if response.status_code >= 300:
            message = extract_provider_error(result) or response.text
            raise NetworkException(
                "Failed to broadcast Ethereum transaction using MyEtherWallet: "
                f"{message}"
            )

        error = extract_provider_error(result)
        if error is not None:
            raise NetworkException(
                "Failed to broadcast Ethereum transaction using MyEtherWallet: "
                f"{error}"
            )

        return extract_provider_txid(result) or tx_hash_eth(raw_transaction_hex)

    return await asyncio.to_thread(_broadcast)
