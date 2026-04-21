from ...utils.keccak import Keccak256


def extract_raw_transaction(raw_transaction_hex):
    if isinstance(raw_transaction_hex, dict):
        for key in ("raw_transaction", "rawTransaction"):
            if key in raw_transaction_hex:
                return extract_raw_transaction(raw_transaction_hex[key])

    for attr in ("raw_transaction", "rawTransaction"):
        if hasattr(raw_transaction_hex, attr):
            return extract_raw_transaction(getattr(raw_transaction_hex, attr))

    return raw_transaction_hex


def normalize_raw_transaction(raw_transaction_hex):
    raw_transaction_hex = extract_raw_transaction(raw_transaction_hex)

    if isinstance(raw_transaction_hex, (bytes, bytearray)):
        raw_bytes = bytes(raw_transaction_hex)
        if raw_bytes.startswith(b"0x"):
            try:
                return bytes.fromhex(raw_bytes[2:].decode()).hex()
            except ValueError:
                pass

        try:
            decoded = raw_bytes.decode()
        except UnicodeDecodeError:
            return raw_bytes.hex()

        raw_transaction_hex = decoded

    if not isinstance(raw_transaction_hex, str):
        raise TypeError("Unsupported Ethereum transaction payload")

    normalized = (
        raw_transaction_hex[2:]
        if raw_transaction_hex.startswith("0x")
        else raw_transaction_hex
    )
    try:
        bytes.fromhex(normalized)
    except ValueError:
        normalized = raw_transaction_hex.encode().hex()
    return normalized


def tx_hash_eth(raw_transaction_hex):
    normalized = normalize_raw_transaction(raw_transaction_hex)
    return "0x" + Keccak256(bytes.fromhex(normalized)).hexdigest()


def normalize_provider_txid(txid):
    if not isinstance(txid, str):
        return None

    normalized = txid[2:] if txid.startswith("0x") else txid
    try:
        bytes.fromhex(normalized)
    except ValueError:
        return None
    return "0x" + normalized.lower()


def extract_provider_txid(payload):
    if isinstance(payload, dict):
        tx = payload.get("tx")
        candidates = [
            payload.get("result"),
            payload.get("hash"),
            payload.get("txid"),
            payload.get("txHash"),
        ]
        if isinstance(tx, dict):
            candidates.extend([tx.get("hash"), tx.get("txid"), tx.get("txHash")])

        for candidate in candidates:
            normalized = normalize_provider_txid(candidate)
            if normalized is not None:
                return normalized
        return None

    return normalize_provider_txid(payload)


def extract_provider_error(payload):
    if not isinstance(payload, dict):
        return None

    error = payload.get("error")
    if error:
        if isinstance(error, dict):
            return error.get("message") or str(error)
        return str(error)

    if payload.get("success") is False:
        return payload.get("message") or "provider reported failure"

    if payload.get("status") in ("0", 0, False):
        return payload.get("message") or payload.get("result") or "provider reported failure"

    return None
