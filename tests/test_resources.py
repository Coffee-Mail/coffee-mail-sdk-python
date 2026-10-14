from typing import Any

from coffeemail.core.errors import NotFoundError
from coffeemail.core.types import CoffeeMailResponse
from coffeemail.resources.domains import Domains
from coffeemail.resources.suppressions import Suppressions
from coffeemail.resources.webhooks import Webhooks


class FakeTransport:
    """Transporte que registra a chamada e devolve uma resposta pronta."""

    def __init__(self, payload: Any = None, error: Any = None, status_code: int = 200) -> None:
        self.payload = payload
        self.error = error
        self.status_code = status_code
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        path: str,
        params: Any = None,
        json_data: Any = None,
    ) -> CoffeeMailResponse[Any]:
        self.calls.append(
            {"method": method, "path": path, "params": params, "json_data": json_data}
        )
        return CoffeeMailResponse(data=self.payload, error=self.error, status_code=self.status_code)


def test_suppressions_list_omite_parametros_nao_informados() -> None:
    transport = FakeTransport(payload={"suppressions": [], "nextCursor": None})
    res = Suppressions(transport)  # type: ignore[arg-type]

    res.list()

    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["path"] == "/v1/product/suppressions"
    assert transport.calls[0]["params"] == {}


def test_suppressions_list_repassa_paginacao() -> None:
    transport = FakeTransport(payload={"suppressions": [], "nextCursor": None})

    Suppressions(transport).list(limit=25, after="cur_1")  # type: ignore[arg-type]

    assert transport.calls[0]["params"] == {"limit": 25, "after": "cur_1"}


def test_suppressions_check_remove_espacos_do_email() -> None:
    transport = FakeTransport(payload={"suppressed": False})

    Suppressions(transport).check("  alguem@dominio.com  ")  # type: ignore[arg-type]

    assert transport.calls[0]["path"] == "/v1/product/suppressions/alguem@dominio.com"


def test_suppressions_create_usa_manual_como_motivo_padrao() -> None:
    transport = FakeTransport(
        payload={
            "id": "sup_1",
            "email": "x@dominio.com",
            "reason": "manual",
            "createdAt": "2026-01-01T00:00:00Z",
        }
    )

    Suppressions(transport).create("  x@dominio.com ")  # type: ignore[arg-type]

    assert transport.calls[0]["json_data"] == {"email": "x@dominio.com", "reason": "manual"}


def test_erro_do_transporte_nao_vira_dado_valido() -> None:
    transport = FakeTransport(payload=None, error=NotFoundError("nao encontrado"), status_code=404)

    out = Suppressions(transport).check("sumiu@dominio.com")  # type: ignore[arg-type]

    assert out.data is None
    assert out.error is not None
    assert out.status_code == 404


def test_resposta_sem_corpo_nao_e_tratada_como_sucesso_com_dado() -> None:
    transport = FakeTransport(payload=None, error=None, status_code=200)

    out = Suppressions(transport).list()  # type: ignore[arg-type]

    assert out.data is None
    assert out.error is None


def test_webhooks_list_usa_o_caminho_do_produto() -> None:
    transport = FakeTransport(payload={"webhooks": []})

    Webhooks(transport).list()  # type: ignore[arg-type]

    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["path"].startswith("/v1/product/webhooks")


class FakeListTransport(FakeTransport):
    """Transporte que tambem responde ao caminho de array (request_list)."""

    def request_list(
        self,
        method: str,
        path: str,
        json_data: Any = None,
    ) -> CoffeeMailResponse[Any]:
        self.calls.append({"method": method, "path": path, "json_data": json_data})
        return CoffeeMailResponse(data=self.payload, error=self.error, status_code=self.status_code)


def test_send_batch_envia_array_puro_e_le_array_de_volta() -> None:
    from coffeemail.resources.emails import Emails

    transport = FakeListTransport(
        payload=[
            {"ok": True, "data": {"id": "em_1", "status": "queued", "queuedAt": "2026-10-09"}},
            {"ok": False, "error": "destinatário suprimido"},
        ],
        status_code=202,
    )
    emails = Emails(transport)  # type: ignore[arg-type]

    result = emails.send_batch(
        [
            {"from": "a@x.com", "to": "b@x.com", "subject": "s", "html": "<p>h</p>"},
            {"from": "a@x.com", "to": "c@x.com", "subject": "s", "html": "<p>h</p>"},
        ]
    )

    enviado = transport.calls[0]["json_data"]
    assert isinstance(enviado, list), "a spec exige array puro, nao {'items': [...]}"
    assert len(enviado) == 2

    assert result.error is None
    assert result.data is not None
    assert len(result.data) == 2
    assert result.data[0].ok is True
    assert result.data[1].ok is False


def test_send_batch_preserva_queued_at_do_envelope() -> None:
    from coffeemail.resources.emails import Emails

    transport = FakeListTransport(
        payload=[
            {"ok": True, "data": {"id": "em_1", "status": "queued", "queuedAt": "2026-10-09"}}
        ],
        status_code=202,
    )
    emails = Emails(transport)  # type: ignore[arg-type]

    result = emails.send_batch([{"from": "a@x.com", "to": "b@x.com", "subject": "s", "html": "h"}])

    assert result.data is not None
    item = result.data[0]
    assert item.ok is True
    assert item.data.queued_at == "2026-10-09"


def _dns_check(ok: bool, resolution: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "resolution": resolution,
        "expected": "v=spf1 include:coffeemail.com.br ~all",
        "got": None,
        "matches": [],
    }


def test_domains_verify_repassa_status_reason_identidade_e_resolution() -> None:
    transport = FakeTransport(
        payload={
            "id": "dom_123",
            "name": "empresa.com.br",
            "status": "pending",
            "statusReason": "provider_pending",
            "sendingIdentity": {
                "provider": "aws_ses",
                "state": "pending",
                "lastSyncedAt": "2026-10-14T12:00:00.000Z",
            },
            "verifiedAt": None,
            "createdAt": "2026-10-01T00:00:00.000Z",
            "checks": {
                "spf": _dns_check(True, "found"),
                "dkim": _dns_check(True, "found"),
                "dmarc": _dns_check(True, "found"),
                "ownership": _dns_check(False, "unknown"),
                "infrastructureSpf": _dns_check(False, "absent"),
            },
            "requiredChecks": ["spf", "dkim", "dmarc", "ownership"],
        }
    )

    res = Domains(transport).verify("dom_123")  # type: ignore[arg-type]

    assert res.data is not None
    assert res.data.status == "pending"
    assert res.data.status_reason == "provider_pending"
    assert res.data.sending_identity is not None
    assert res.data.sending_identity.provider == "aws_ses"
    assert res.data.sending_identity.state == "pending"
    assert res.data.sending_identity.last_synced_at == "2026-10-14T12:00:00.000Z"
    assert res.data.checks is not None
    assert res.data.checks["spf"].resolution == "found"
    assert res.data.checks["ownership"].resolution == "unknown"
    assert res.data.checks["infrastructureSpf"].resolution == "absent"


def test_domains_get_aceita_resposta_sem_os_campos_novos() -> None:
    transport = FakeTransport(
        payload={
            "id": "dom_123",
            "name": "empresa.com.br",
            "status": "verified",
            "createdAt": "2026-10-01T00:00:00.000Z",
            "campoDesconhecido": "ignorado",
        }
    )

    res = Domains(transport).get("dom_123")  # type: ignore[arg-type]

    assert res.data is not None
    assert res.data.status_reason is None
    assert res.data.sending_identity is None
    assert res.data.checks is None


def test_domains_list_repassa_status_reason() -> None:
    transport = FakeTransport(
        payload={
            "domains": [
                {
                    "id": "dom_123",
                    "name": "empresa.com.br",
                    "status": "failed",
                    "statusReason": "dns_records_missing",
                    "createdAt": "2026-10-01T00:00:00.000Z",
                }
            ]
        }
    )

    res = Domains(transport).list()  # type: ignore[arg-type]

    assert res.data is not None
    assert res.data.domains[0].status_reason == "dns_records_missing"
