from statistics import median
from .fullnode import EthereumWeb3FeeEstimator
from ...errors import NetworkException
from ...nodes.eth import eth_nodes


class EthereumFeeEstimator:
    """
    A class representing a Ethereum gas estimator.

    Developers should use this class, because it autoselects the most stable
    providers to fetch data from.
    """

    def __init__(self, **kwargs):
        self.provider_list = []
        fullnode_endpoints = kwargs.get("fullnode_endpoints")

        if not fullnode_endpoints:
            fullnode_endpoints = [] + eth_nodes

        for endpoint in fullnode_endpoints:
            self.provider_list.append(EthereumWeb3FeeEstimator(**endpoint))

    def estimate_gas(self, transaction_obj):
        """
        Gets the gas required for a particular transaction.

        Returns:
            int: The gas required for the transaction.

        Raises:
            NetworkException: If the API request fails or the gas cannot be retrieved.
        """
        fee_rates = []

        for provider in self.provider_list:
            try:
                fee_rate = provider.estimate_gas(transaction_obj)
                fee_rates.append(fee_rate)
            except NetworkException:
                continue

        # Return the median fee rate from all collected rates
        return median(fee_rates)
