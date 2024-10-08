from statistics import median
from .blockcypher import BlockcypherFeeEstimator
from .fullnode import DogecoinRPCClient
from ...errors import NetworkException
from ...nodes.dash import dash_nodes


class DogecoinFeeEstimator:
    """
    A class representing a Dogecoin fee rate estimator.

    Developers should use this class, because it autoselects the most stable
    providers to fetch data from.
    """

    def __init__(self, **kwargs):
        self.provider_list = []
        fullnode_endpoints = kwargs.get("fullnode_endpoints") or []
        fullnode_endpoints += dash_nodes
        blockcypher_tokens = kwargs.get("blockcypher_tokens")

        tokens = blockcypher_tokens
        if not tokens:
            tokens = []
        for token in tokens:
            self.provider_list.append(BlockcypherFeeEstimator(api_key=token))
        self.provider_list.append(BlockcypherFeeEstimator())  # No token (free) version
        for endpoint in fullnode_endpoints:
            self.provider_list.append(DogecoinRPCClient(**endpoint))

    def get_fee_rate(self):
        """
        Gets the network fee rate.

        Returns:
            int: The network fee rate.

        Raises:
            Exception: If none of the fee providers are working after the specified number of tries.
        """
        fee_rates = []

        for provider in self.provider_list:
            try:
                fee_rate = provider.get_fee_rate()
                fee_rates.append(fee_rate)
            except NetworkException:
                continue

        # Return the median fee rate from all collected rates
        return median(fee_rates)
