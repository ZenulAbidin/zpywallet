from .esplora import EsploraAddress


class MempoolSpaceAddress(EsploraAddress):
    """
    A class representing a list of Bitcoin addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a Bitcoin address using Mempool.space.
    """

    def __init__(self, addresses, request_interval=(3, 1), transactions=None, **kwargs):
        super().__init__(
            addresses,
            request_interval=request_interval,
            transactions=transactions,
            url="https://mempool.space/api/v1",
            **kwargs
        )
