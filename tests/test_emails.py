from coffeemail.models.emails import EmailParticipant, SendEmailPayload
from coffeemail.resources.emails import (
    _build_send_payload,
    _normalize_participant,
    _normalize_participants,
)


def test_normalize_participant_from_string() -> None:
    res = _normalize_participant("teste@dominio.com")
    assert res == {"email": "teste@dominio.com"}


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
    assert wire["to"] == {"email": "cliente@empresa.com"}
    assert wire["subject"] == "Boas-vindas!"
    assert wire["html"] == "<h1>Olá</h1>"
