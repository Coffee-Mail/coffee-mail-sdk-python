import hashlib
import hmac


def verify_webhook_signature(
    payload: str | bytes,
    signature: str,
    secret: str,
) -> bool:
    if not payload or not signature or not secret:
        return False

    try:
        raw_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        secret_bytes = secret.encode("utf-8")
        computed = hmac.new(secret_bytes, raw_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed.lower(), signature.strip().lower())
    except Exception:
        return False
