from .esplora import EsploraAddress

class BlockstreamAddress(EsploraAddress):
    def __init__(self, addresses, request_interval=(3,1), transactions=None, **kwargs):
        super().__init__(addresses, request_interval=request_interval, transactions=transactions, url="https://blockstream.info/testnet/api", **kwargs)