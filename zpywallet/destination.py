from .utils.keys import PublicKey
from .utils.base58 import b58decode_check
from .utils.bech32 import bech32_decode
# Amounts are always described internally in the lowest possible denomination
# to make them integers.
class Destination:
    def __init__(self, network, address, amount, in_standard_units=False):
        self._network = network
        self._address = address
        if in_standard_units:
            if network.SUPPORTS_EVM:
                self._amount = int(amount * 1e18)
            else:
                self._amount = int(amount * 1e8)
        else:
            self._amount = amount
        
        self._script_pubkey = PublicKey.script(address, network)
                

    def address(self):
        return self._address
    
    def amount(self):
        return self._amount
    
    def script_pubkey(self):
        return self._script_pubkey

# destination has no attribute script_pubkey.... line 228, encode.py