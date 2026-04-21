import hashlib


def normalize_raw_transaction_bytes(raw_transaction):
    if isinstance(raw_transaction, str):
        normalized = (
            raw_transaction[2:] if raw_transaction.startswith("0x") else raw_transaction
        )
        return bytes.fromhex(normalized)

    if isinstance(raw_transaction, (bytes, bytearray)):
        raw_bytes = bytes(raw_transaction)
        if raw_bytes.startswith(b"0x"):
            return bytes.fromhex(raw_bytes[2:].decode())

        try:
            decoded = raw_bytes.decode()
        except UnicodeDecodeError:
            return raw_bytes

        normalized = decoded[2:] if decoded.startswith("0x") else decoded
        try:
            return bytes.fromhex(normalized)
        except ValueError:
            return raw_bytes

    raise TypeError("Unsupported raw transaction payload")


def tx_hash_bitcoin_like(raw_transaction):
    raw_bytes = normalize_raw_transaction_bytes(raw_transaction)
    return hashlib.sha256(hashlib.sha256(raw_bytes).digest()).digest()[::-1].hex()
