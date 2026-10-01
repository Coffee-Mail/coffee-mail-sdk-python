import hashlib
import hmac

from coffeemail.core.crypto import verify_webhook_signature
from coffeemail.resources.webhooks import Webhooks


def test_verify_webhook_signature_valid() -> None:
    secret = "whsec_test_secret_key"
    payload = '{"event":"email.delivered","id":"evt_123"}'
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    assert verify_webhook_signature(payload, signature, secret) is True
    assert Webhooks.verify_signature(payload, signature, secret) is True


def test_verify_webhook_signature_invalid() -> None:
    secret = "whsec_test_secret_key"
    payload = '{"event":"email.delivered"}'
    tampered_signature = "bad_signature_hash"

    assert verify_webhook_signature(payload, tampered_signature, secret) is False


def test_verify_webhook_signature_empty_inputs() -> None:
    assert verify_webhook_signature("", "sig", "sec") is False
    assert verify_webhook_signature("body", "", "sec") is False
    assert verify_webhook_signature("body", "sig", "") is False
