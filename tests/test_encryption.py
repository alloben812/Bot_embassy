from app.core.encryption import decrypt, decrypt_optional, encrypt, encrypt_optional


def test_encrypt_decrypt_roundtrip() -> None:
    payload = "user@example.com:hunter2"
    token = encrypt(payload)
    assert isinstance(token, bytes)
    assert decrypt(token) == payload


def test_encrypt_decrypt_unicode() -> None:
    payload = "Иван Петров — паспорт 75 1234567"
    assert decrypt(encrypt(payload)) == payload


def test_encrypt_optional_none() -> None:
    assert encrypt_optional(None) is None
    assert decrypt_optional(None) is None


def test_encrypt_optional_some() -> None:
    token = encrypt_optional("abc")
    assert token is not None
    assert decrypt_optional(token) == "abc"
