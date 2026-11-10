"""Password hashing (Argon2id) and JWT access tokens. Refresh tokens are opaque and stored hashed."""
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import Settings
from app.core.exceptions import unauthenticated

_hasher = PasswordHasher()
# Verified against when the account does not exist, so response time does not reveal existence.
_DUMMY_HASH = _hasher.hash("not-a-real-password-for-timing-equalisation")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class AccessClaims:
    user_id: uuid.UUID
    role: str
    session_id: uuid.UUID
    jti: str
    expires_at: datetime


def create_access_token(
    settings: Settings, *, user_id: uuid.UUID, role: str, session_id: uuid.UUID
) -> tuple[str, AccessClaims]:
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=settings.jwt_access_ttl_min)
    jti = uuid.uuid4().hex
    payload = {"sub": str(user_id), "role": role, "sid": str(session_id), "jti": jti,
               "iat": int(now.timestamp()), "exp": int(exp.timestamp()), "typ": "access"}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, AccessClaims(user_id, role, session_id, jti, exp)


def decode_access_token(settings: Settings, token: str) -> AccessClaims:
    try:
        p = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                       options={"require": ["exp", "sub", "jti", "sid", "typ"]})
        if p["typ"] != "access":
            raise jwt.InvalidTokenError("wrong token type")
        return AccessClaims(uuid.UUID(p["sub"]), p["role"], uuid.UUID(p["sid"]), p["jti"],
                            datetime.fromtimestamp(p["exp"], UTC))
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise unauthenticated("Invalid or expired token.") from exc
