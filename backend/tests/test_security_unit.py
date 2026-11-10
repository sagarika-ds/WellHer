import base64
import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.crypto import DecryptionError, FieldCipher
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_token,
    new_opaque_token,
    verify_password,
)


def test_password_hash_is_argon2id_and_verifies():
    h = hash_password("correct horse battery staple")
    assert h.startswith("$argon2id$")
    assert verify_password(h, "correct horse battery staple")
    assert not verify_password(h, "wrong")


def test_verify_with_unknown_account_is_false_not_error():
    assert verify_password(None, "anything") is False


def test_hashes_are_salted():
    assert hash_password("same-password-1") != hash_password("same-password-1")


def test_access_token_roundtrip():
    s = get_settings()
    uid, sid = uuid.uuid4(), uuid.uuid4()
    token, claims = create_access_token(s, user_id=uid, role="user", session_id=sid)
    got = decode_access_token(s, token)
    assert (got.user_id, got.session_id, got.role, got.jti) == (uid, sid, "user", claims.jti)


def test_tampered_and_expired_tokens_rejected():
    s = get_settings()
    token, _ = create_access_token(s, user_id=uuid.uuid4(), role="user", session_id=uuid.uuid4())
    with pytest.raises(AppError):
        decode_access_token(s, token[:-3] + "abc")
    expired = jwt.encode({"sub": str(uuid.uuid4()), "role": "user", "sid": str(uuid.uuid4()), "jti": "x",
                          "typ": "access", "exp": int(time.time()) - 10}, s.jwt_secret, algorithm="HS256")
    with pytest.raises(AppError):
        decode_access_token(s, expired)


def test_wrong_signature_and_wrong_type_rejected():
    s = get_settings()
    base = {"sub": str(uuid.uuid4()), "role": "user", "sid": str(uuid.uuid4()), "jti": "x",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())}
    for payload, key in (({**base, "typ": "access"}, "a-different-secret-" + "y" * 30),
                         ({**base, "typ": "refresh"}, s.jwt_secret)):
        with pytest.raises(AppError):
            decode_access_token(s, jwt.encode(payload, key, algorithm="HS256"))


def test_alg_none_rejected():
    s = get_settings()
    t = jwt.encode({"sub": str(uuid.uuid4()), "role": "admin", "sid": str(uuid.uuid4()), "jti": "x",
                    "typ": "access", "exp": int(time.time()) + 300}, key=None, algorithm="none")
    with pytest.raises(AppError):
        decode_access_token(s, t)


def test_opaque_tokens_unique_and_hash_deterministic():
    a, b = new_opaque_token(), new_opaque_token()
    assert a != b and len(a) >= 60
    assert hash_token(a) == hash_token(a) != hash_token(b)


def test_field_cipher_roundtrip_and_randomised():
    c = FieldCipher(b"k" * 32)
    t1, t2 = c.encrypt("private note"), c.encrypt("private note")
    assert t1 != t2 and t1.startswith("k1:") and "private" not in t1
    assert c.decrypt(t1) == c.decrypt(t2) == "private note"
    assert c.decrypt(c.encrypt("नमस्ते ಕನ್ನಡ తెలుగు")) == "नमस्ते ಕನ್ನಡ తెలుగు"


def test_field_cipher_detects_tampering_and_wrong_key():
    c = FieldCipher(b"k" * 32)
    t = c.encrypt("note")
    raw = bytearray(base64.b64decode(t[3:]))
    raw[-1] ^= 1
    with pytest.raises(DecryptionError):
        c.decrypt("k1:" + base64.b64encode(bytes(raw)).decode())
    with pytest.raises(DecryptionError):
        FieldCipher(b"z" * 32).decrypt(t)
    with pytest.raises(DecryptionError):
        c.decrypt("k9:" + t[3:])


def _kw(**over):
    base = dict(database_url="postgresql+asyncpg://x", jwt_secret="s" * 40,
                field_encryption_key=base64.b64encode(b"k" * 32).decode(), _env_file=None)
    base.update(over)
    return base


def test_settings_reject_bad_secrets_and_placeholders():
    Settings(**_kw())
    with pytest.raises(ValidationError):
        Settings(**_kw(jwt_secret="short"))
    with pytest.raises(ValidationError):
        Settings(**_kw(field_encryption_key="CHANGE_ME_BASE64_32_BYTES"))
    with pytest.raises(ValidationError):
        Settings(**_kw(field_encryption_key=base64.b64encode(b"k" * 16).decode()))
    with pytest.raises(ValidationError):
        Settings(**_kw(app_env="production", jwt_secret="CHANGE_ME" + "x" * 40))
    with pytest.raises(ValidationError):
        Settings(**_kw(app_env="production", events_inline=True))
    with pytest.raises(ValidationError):
        Settings(**_kw(app_env="production", email_backend="console"))
