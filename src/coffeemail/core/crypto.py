"""Verificação da assinatura das entregas de webhook da CoffeeMail.

A assinatura é ``sha256=`` + HMAC-SHA256 em hexadecimal minúsculo de
``timestamp + "." + idempotencyKey + "." + corpo bruto``, usando o segredo do webhook
(``whsec_...``) como bytes UTF-8. Entregas fora da janela de tolerância (padrão de 300s)
são rejeitadas para impedir replay.
"""

import hashlib
import hmac
import re
import time
from collections.abc import Callable, Mapping

HEADER_SIGNATURE = "x-webhook-signature"
HEADER_TIMESTAMP = "x-webhook-timestamp"
HEADER_IDEMPOTENCY_KEY = "x-webhook-idempotency-key"
HEADER_TEST = "x-webhook-test"
DEFAULT_TOLERANCE_SECONDS = 300
SIGNATURE_PREFIX = "sha256="
_SEPARATOR = b"."
_UNIX_SECONDS = re.compile(r"^-?\d{1,18}$")


def _raw_bytes(payload: str | bytes) -> bytes:
    return payload.encode("utf-8") if isinstance(payload, str) else payload


def _header(headers: Mapping[str, str] | None, name: str) -> str | None:
    if headers is None:
        return None
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def sign_webhook(payload: str | bytes, secret: str, timestamp: str, idempotency_key: str) -> str:
    """Calcula a assinatura esperada de uma entrega. Útil para testar o seu handler."""
    content = (
        timestamp.encode("utf-8")
        + _SEPARATOR
        + idempotency_key.encode("utf-8")
        + _SEPARATOR
        + _raw_bytes(payload)
    )
    digest = hmac.new(secret.encode("utf-8"), content, hashlib.sha256).hexdigest()
    return SIGNATURE_PREFIX + digest


def _within_tolerance(timestamp: str, tolerance_seconds: int, now: Callable[[], float]) -> bool:
    raw = timestamp.strip()
    if not _UNIX_SECONDS.match(raw):
        return False
    return abs(int(now()) - int(raw)) <= tolerance_seconds


def verify_webhook_signature(
    payload: str | bytes,
    secret: str,
    *,
    headers: Mapping[str, str] | None = None,
    signature: str | None = None,
    timestamp: str | None = None,
    idempotency_key: str | None = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Callable[[], float] = time.time,
) -> bool:
    """Confere assinatura e janela de tolerância de uma entrega de webhook.

    Informe os headers da requisição (``headers=request.headers``) ou os valores
    ``signature``, ``timestamp`` e ``idempotency_key`` diretamente. ``payload`` deve ser
    o corpo bruto, exatamente como recebido.
    """
    resolved_signature = signature or _header(headers, HEADER_SIGNATURE)
    resolved_timestamp = timestamp or _header(headers, HEADER_TIMESTAMP)
    resolved_key = idempotency_key or _header(headers, HEADER_IDEMPOTENCY_KEY)
    if not secret or not resolved_signature or not resolved_timestamp or not resolved_key:
        return False
    if not _within_tolerance(resolved_timestamp, tolerance_seconds, now):
        return False
    expected = sign_webhook(payload, secret, resolved_timestamp, resolved_key)
    return hmac.compare_digest(expected.encode("utf-8"), resolved_signature.encode("utf-8"))
