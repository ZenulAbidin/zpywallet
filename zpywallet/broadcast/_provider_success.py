from ._tx_hash import tx_hash_bitcoin_like


def bitcoin_like_broadcast_success_txid(raw_transaction_hex):
    return tx_hash_bitcoin_like(raw_transaction_hex)
