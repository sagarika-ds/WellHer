# Diagram 18: Authentication and Authorization Sequence

> **Implementation status:** Implemented and tested end to end (backend + the mobile client against a live backend); matches the code.

## Diagram source (Mermaid)

```mermaid
sequenceDiagram
    actor U as User
    participant M as Mobile
    participant C as Core backend
    participant R as Redis
    participant DB as PostgreSQL
    U->>M: email + password
    M->>C: POST /auth/login
    C->>DB: load user, verify Argon2 hash
    C->>DB: store refresh token jti + device
    C-->>M: access JWT (15 min) + refresh token
    M->>M: save in secure store
    M->>C: GET /cycles (Bearer access)
    C->>R: check denylist (token id + session id)
    C->>C: verify signature, role, ownership
    C->>C: check consent: health_tracking
    C->>DB: query WHERE user_id = me
    C-->>M: 200 data
    Note over M,C: access token expires
    M->>C: POST /auth/refresh
    C->>DB: validate jti, rotate token
    C-->>M: new access + new refresh
    U->>M: logout
    M->>C: POST /auth/logout
    C->>R: denylist access jti
    C->>DB: revoke refresh token
```

## Components

- **Login**: Verifies Argon2 hash; issues short-lived access JWT and rotating refresh token.
- **Refresh rotation**: Each refresh invalidates the old token; reuse of an old token revokes the session family.
- **Denylist**: Redis set of revoked access token IDs until expiry.
- **Ownership + consent**: Checked on every protected route.

## Data flow

Credentials -> tokens -> authenticated calls -> silent refresh -> logout revokes both tokens.

## Technologies and why they were selected

- **JWT (HS256 or RS256)**: Stateless access checks.
- **Argon2**: Resistant to GPU cracking.
- **expo-secure-store**: OS-backed secret storage on device.

## Communication with other modules

Mobile <-> core only.

## Security considerations

Rate-limited login, generic error messages, refresh reuse detection, audit entries for login/logout/failures.

## Real-world execution example

Stolen old refresh token is replayed: backend detects reuse, revokes the family, and the user must log in again.
