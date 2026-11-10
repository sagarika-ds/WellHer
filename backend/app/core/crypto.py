"""Application-level field encryption (AES-256-GCM).

Format: "k1:" + base64(nonce[12] || ciphertext+tag). The key id prefix allows adding key rotation later.
LIMITATION: the data key comes from an environment variable. True envelope encryption with a managed
KMS (wrapping per-user data keys) is a production hardening step, not implemented in this milestone.
"""
import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

KEY_ID = "k1"


class DecryptionError(Exception):
    pass


class FieldCipher:
    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("key must be 32 bytes")
        self._aes = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, plaintext.encode(), None)
        return f"{KEY_ID}:" + base64.b64encode(nonce + ct).decode()

    def decrypt(self, token: str) -> str:
        try:
            kid, _, body = token.partition(":")
            if kid != KEY_ID:
                raise DecryptionError("unknown key id")
            raw = base64.b64decode(body)
            return self._aes.decrypt(raw[:12], raw[12:], None).decode()
        except (InvalidTag, ValueError) as exc:
            raise DecryptionError("ciphertext invalid or tampered") from exc


def get_cipher() -> FieldCipher:
    return FieldCipher(base64.b64decode(get_settings().field_encryption_key))


class EncryptedText(TypeDecorator):
    """Transparent AES-GCM encryption for free-text columns."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else get_cipher().encrypt(value)

    def process_result_value(self, value, dialect):
        return None if value is None else get_cipher().decrypt(value)
