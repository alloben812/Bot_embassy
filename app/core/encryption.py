from cryptography.fernet import Fernet

from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.bot_encryption_key.encode())
    return _fernet


def encrypt(plaintext: str) -> bytes:
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    return _get_fernet().decrypt(ciphertext).decode("utf-8")


def encrypt_optional(plaintext: str | None) -> bytes | None:
    return encrypt(plaintext) if plaintext else None


def decrypt_optional(ciphertext: bytes | None) -> str | None:
    return decrypt(ciphertext) if ciphertext else None
