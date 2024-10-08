import requests
from ...errors import NetworkException


class BlockcypherFeeEstimator:
    """
    A class representing a Bitcoin fee rate estimator using Blockcypher.
    """

    def __init__(self, request_interval=(3, 1), api_key=None):
        """
        Initializes an instance of the BlockcypherFeeEstimator class.

        Args:
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0, N) for no rate limiting, where N > 0.
            api_key (str): The API key for accessing the Blockcypher API.
        """
        self.requests, self.interval_sec = request_interval
        self.api_key = api_key

    def get_fee_rate(self):
        """
        Retrieves the current fee rate for Bitcoin transactions.

        Raises:
            NetworkException: If the API request fails or the fee rate cannot be retrieved
        """
        # Define the default API URL within the method for Blockcypher:
        api_url = "https://api.blockcypher.com/v1/btc/main"

        params = None
        if self.api_key:
            params = {"token", self.api_key}

        # Get the current fee rate from the specified API:
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(api_url, params=params, timeout=60)
                break
            except requests.RequestException:
                pass
            except requests.exceptions.JSONDecodeError:
                pass

        if response.status_code == 200:
            data = response.json()
            fee_rate_kb = data["high_fee_per_kb"]
            fee_rate_vbyte = fee_rate_kb / 1000  # Convert to sats/vByte
            return fee_rate_vbyte
        else:
            raise NetworkException(
                "Failed to retrieve current fee rate from Blockcypher"
            )
