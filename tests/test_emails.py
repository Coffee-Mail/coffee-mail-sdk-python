from coffeemail.models.emails import EmailParticipant, SendEmailPayload
from coffeemail.resources.emails import (
    _build_send_payload,
    _normalize_participant,
    _normalize_participants,
)


def test_normalize_participant_from_string() -> None:
    res = _normalize_participant("teste@dominio.com")
    assert res == {"email": "teste@dominio.com"}


def test_normalize_participant_from_named_string() -> None:
    res = _normalize_participant("Empresa Teste <contato@empresa.com>")
    assert res == {"email": "contato@empresa.com", "name": "Empresa Teste"}


def test_normalize_participant_from_model() -> None:
    model = EmailParticipant(email="suporte@dominio.com", name="Suporte CoffeeMail")
    res = _normalize_participant(model)
    assert res == {"email": "suporte@dominio.com", "name": "Suporte CoffeeMail"}


def test_normalize_participants_list() -> None:
    raw: list[str | dict[str, object]] = ["a@dominio.com", {"email": "b@dominio.com", "name": "B"}]
    res = _normalize_participants(raw)
    assert res is not None
    assert len(res) == 2
    assert res[0] == {"email": "a@dominio.com"}
    assert res[1] == {"email": "b@dominio.com", "name": "B"}


def test_build_send_payload_from_model() -> None:
    payload = SendEmailPayload(
        from_address="contato@empresa.com",
        to="cliente@empresa.com",
        subject="Boas-vindas!",
        html="<h1>Olá</h1>",
    )
    wire = _build_send_payload(payload)
    assert wire["from"] == {"email": "contato@empresa.com"}
    assert wire["to"] == [{"email": "cliente@empresa.com"}]
    assert wire["subject"] == "Boas-vindas!"
    assert wire["html"] == "<h1>Olá</h1>"


def test_to_is_always_a_list_even_for_a_single_recipient() -> None:
    wire = _build_send_payload(
        {
            "from": "contato@empresa.com",
            "to": "cliente@empresa.com",
            "subject": "x",
            "html": "<p>x</p>",
        }
    )
    assert isinstance(wire["to"], list)


def test_reply_to_is_a_single_object_not_a_list() -> None:
    wire = _build_send_payload(
        {
            "from": "contato@empresa.com",
            "to": ["cliente@empresa.com"],
            "replyTo": "suporte@empresa.com",
            "subject": "x",
            "html": "<p>x</p>",
        }
    )
    assert wire["replyTo"] == {"email": "suporte@empresa.com"}


def test_error_envelope_is_unwrapped_from_the_nested_error_object() -> None:
    from coffeemail.core.errors import ValidationError, create_error_from_response

    error = create_error_from_response(
        400,
        {
            "error": {
                "message": "Destinatário inválido",
                "code": "VALIDATION_FAILED",
                "details": {"field": "to"},
            }
        },
        fallback_message="fallback",
    )

    assert isinstance(error, ValidationError)
    assert error.message == "Destinatário inválido"
    assert error.code == "VALIDATION_ERROR"
    assert error.api_code == "VALIDATION_FAILED"
    assert error.details == {"field": "to"}


def test_error_envelope_still_reads_a_root_message() -> None:
    from coffeemail.core.errors import NotFoundError, create_error_from_response

    error = create_error_from_response(404, {"message": "não encontrado"}, fallback_message="x")

    assert isinstance(error, NotFoundError)
    assert error.message == "não encontrado"
    assert error.code == "NOT_FOUND"


def test_payload_fields_follow_the_contract() -> None:
    wire = _build_send_payload(
        SendEmailPayload(
            from_address="a@b.com",
            to="c@d.com",
            subject="x",
            text="x",
            email_type="broadcast",
            suppression_category="newsletter",
            metadata={"pedido": 1},
            idempotency_key="k1",
            sandbox=True,
        )
    )
    assert wire["emailType"] == "broadcast"
    assert wire["suppressionCategory"] == "newsletter"
    assert wire["metadata"] == {"pedido": 1}
    for header_only in ("idempotencyKey", "idempotency_key", "sandbox", "trackOpens"):
        assert header_only not in wire


def test_dict_payload_drops_header_only_keys() -> None:
    wire = _build_send_payload(
        {
            "from": "a@b.com",
            "to": "c@d.com",
            "subject": "x",
            "idempotencyKey": "k",
            "isSandbox": True,
        }
    )
    assert "idempotencyKey" not in wire
    assert "isSandbox" not in wire
