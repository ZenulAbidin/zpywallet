from .transaction import Transaction

# NOTE: Currently, UTXO can only detect compressed/uncompressed P2PKH (legacy "1")
# and compressed P2WPKH (bech32 "bc1q") addresses.
class UTXO:
    def __init__(self, transaction: Transaction, index: int, addresses=[], only_mine=False, _unsafe_internal_testing_only=None):
        if _unsafe_internal_testing_only:
            self._output = _unsafe_internal_testing_only
            return
        
        if transaction.network().SUPPORTS_EVM:
            raise ValueError("Blockchain does not support UTXOs")
        
        self._network = transaction.network()
        outputs = transaction.sat_outputs(only_unspent=True)
        try:
            output = outputs[index]
            output['txid'] = transaction.txid()
            #output['index'] = index # should be the same
            if not only_mine or output['address'] in addresses:
                self._output = output
            else:
                raise ValueError("only_mine is specified and UTXO does not belong to this wallet")
        except IndexError as e:
            del(private_keys)
            raise IndexError(f"Transaction output {index} does not exist")
        
    def network(self):
        return self._network

    def txid(self):
        return self._output['txid']
    
    def index(self):
        return self._output['index']

    def amount(self, in_standard_units=True):
        if in_standard_units:
            return self._output['amount'] / 1e8
        else:
            return self._output['amount']
    
    def address(self):
        return self._output['address']

    # Private methods, do not use in user programs.
    def _private_key(self):
        return self._output['private_key']
    
    def _script_pubkey(self):
        return self._output['script_pubkey']