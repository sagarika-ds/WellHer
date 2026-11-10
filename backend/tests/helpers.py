import itertools
from dataclasses import dataclass

PASSWORD = "Tr1cky-Horse-Battery-9"
ALL_CONSENTS = [{"purpose": p, "granted": True}
                for p in ("health_tracking", "ml_processing", "llm_external", "analytics")]
_counter = itertools.count(1)


@dataclass
class Account:
    email: str
    user_id: str
    access: str
    refresh: str

    @property
    def h(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access}"}


async def signup(client, email: str | None = None, consents=ALL_CONSENTS, name: str = "Asha Rao",
                 password: str = PASSWORD) -> Account:
    email = email or f"user{next(_counter)}@example.com"
    r = await client.post("/api/v1/auth/register", json={
        "email": email, "password": password, "display_name": name, "consents": consents})
    assert r.status_code == 201, r.text
    uid = r.json()["id"]
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password, "device": "pytest"})
    assert r.status_code == 200, r.text
    t = r.json()
    return Account(email, uid, t["access_token"], t["refresh_token"])
