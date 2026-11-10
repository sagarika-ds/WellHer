from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

from tests.helpers import signup

API = "/api/v1"


def cyc(start, end=None, **kw):
    return {"start_date": start, **({"end_date": end} if end else {}), **kw}


async def test_cycle_crud_and_computed_length(client):
    acc = await signup(client)
    r1 = await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01", "2026-01-05", flow_intensity=3))
    assert r1.status_code == 201 and r1.json()["cycle_length_days"] is None
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-29"))
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-02-28"))
    rows = (await client.get(f"{API}/cycles", headers=acc.h)).json()
    assert [r["start_date"] for r in rows] == ["2026-02-28", "2026-01-29", "2026-01-01"]  # newest first
    assert [r["cycle_length_days"] for r in rows] == [None, 30, 28]
    cid = r1.json()["id"]
    up = await client.put(f"{API}/cycles/{cid}", headers=acc.h, json=cyc("2026-01-01", "2026-01-06", notes="x"))
    assert up.status_code == 200 and up.json()["end_date"] == "2026-01-06" and up.json()["notes"] == "x"
    assert (await client.delete(f"{API}/cycles/{cid}", headers=acc.h)).status_code == 204
    assert len((await client.get(f"{API}/cycles", headers=acc.h)).json()) == 2


async def test_cycle_stats(client):
    acc = await signup(client)
    empty = (await client.get(f"{API}/cycles/stats", headers=acc.h)).json()
    assert empty["n_cycles"] == 0 and empty["mean_length"] is None
    for d in ("2026-01-01", "2026-01-29", "2026-02-28", "2026-03-27"):  # gaps 28, 30, 27
        await client.post(f"{API}/cycles", headers=acc.h, json=cyc(d))
    s = (await client.get(f"{API}/cycles/stats", headers=acc.h)).json()
    assert s["n_cycles"] == 3 and s["min"] == 27 and s["max"] == 30
    assert s["mean_length"] == pytest.approx(28.33, abs=0.01) and s["std_length"] == pytest.approx(1.53, abs=0.01)


async def test_cycle_validation_and_conflicts(client):
    acc = await signup(client)
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-10", "2026-01-14"))
    cases = {
        400: [cyc("2026-01-10", "2026-01-05"), cyc("2026-01-01", "2026-03-01"),
              cyc((date.today() + timedelta(days=30)).isoformat()), cyc("2026-02-01", flow_intensity=9),
              cyc("garbage")],
        409: [cyc("2026-01-10"), cyc("2026-01-12"), cyc("2026-01-08", "2026-01-11")],
    }
    for code, bodies in cases.items():
        for b in bodies:
            r = await client.post(f"{API}/cycles", headers=acc.h, json=b)
            assert r.status_code == code, (b, r.text)
    assert (await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-15"))).status_code == 201  # adjacent ok


async def test_cycle_filters_and_pagination(client):
    acc = await signup(client)
    for d in ("2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"):
        await client.post(f"{API}/cycles", headers=acc.h, json=cyc(d))
    r = await client.get(f"{API}/cycles", headers=acc.h, params={"date_from": "2026-02-01", "date_to": "2026-03-31"})
    assert [x["start_date"] for x in r.json()] == ["2026-03-01", "2026-02-01"]
    r = await client.get(f"{API}/cycles", headers=acc.h, params={"limit": 2, "offset": 1})
    assert [x["start_date"] for x in r.json()] == ["2026-03-01", "2026-02-01"]
    assert (await client.get(f"{API}/cycles", headers=acc.h, params={"limit": 1000})).status_code == 400


async def test_users_cannot_touch_each_others_records(client):
    a, b = await signup(client), await signup(client)
    cid = (await client.post(f"{API}/cycles", headers=a.h, json=cyc("2026-01-01"))).json()["id"]
    lid = (await client.post(f"{API}/lifestyle", headers=a.h,
                             json={"date": "2026-01-01", "sleep_hours": 7})).json()["id"]
    sid = (await client.post(f"{API}/symptoms", headers=a.h, json={
        "logged_at": "2026-01-01T08:00:00+05:30", "symptom_code": "headache", "severity": 2})).json()["id"]
    assert (await client.get(f"{API}/cycles", headers=b.h)).json() == []
    assert (await client.put(f"{API}/cycles/{cid}", headers=b.h, json=cyc("2026-02-01"))).status_code == 404
    assert (await client.delete(f"{API}/cycles/{cid}", headers=b.h)).status_code == 404
    assert (await client.put(f"{API}/lifestyle/{lid}", headers=b.h,
                             json={"date": "2026-01-01", "sleep_hours": 1})).status_code == 404
    assert (await client.delete(f"{API}/symptoms/{sid}", headers=b.h)).status_code == 404
    assert len((await client.get(f"{API}/cycles", headers=a.h)).json()) == 1  # untouched
    # B can log the same date as A: uniqueness is per user
    assert (await client.post(f"{API}/cycles", headers=b.h, json=cyc("2026-01-01"))).status_code == 201


async def test_symptom_validation_and_flow(client):
    acc = await signup(client)
    good = {"logged_at": "2026-03-01T09:30:00+05:30", "symptom_code": "fatigue", "severity": 3}
    r = await client.post(f"{API}/symptoms", headers=acc.h, json=good)
    assert r.status_code == 201 and r.json()["symptom_code"] == "fatigue"
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    for bad in ({**good, "symptom_code": "made_up"}, {**good, "severity": 6}, {**good, "severity": 0},
                {**good, "logged_at": "2026-03-01T09:30:00"}, {**good, "logged_at": future},
                {**good, "cycle_id": "00000000-0000-0000-0000-000000000000"}):
        assert (await client.post(f"{API}/symptoms", headers=acc.h, json=bad)).status_code == 400, bad
    await client.post(f"{API}/symptoms", headers=acc.h, json={**good, "symptom_code": "headache"})
    only = (await client.get(f"{API}/symptoms", headers=acc.h, params={"symptom_code": "headache"})).json()
    assert len(only) == 1 and only[0]["symptom_code"] == "headache"


async def test_symptom_can_link_own_cycle(client):
    acc = await signup(client)
    cid = (await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01"))).json()["id"]
    r = await client.post(f"{API}/symptoms", headers=acc.h, json={
        "logged_at": "2026-01-02T08:00:00+00:00", "symptom_code": "cramps", "severity": 4, "cycle_id": cid})
    assert r.status_code == 201 and r.json()["cycle_id"] == cid


async def test_lifestyle_unique_per_day_summary_and_validation(client):
    acc = await signup(client)
    today = date.today()
    a = await client.post(f"{API}/lifestyle", headers=acc.h, json={
        "date": today.isoformat(), "sleep_hours": 6, "activity_minutes": 30, "stress_level": 4, "water_ml": 1500})
    assert a.status_code == 201
    assert (await client.post(f"{API}/lifestyle", headers=acc.h, json={"date": today.isoformat()})).status_code == 409
    y = (today - timedelta(days=1)).isoformat()
    b = await client.post(f"{API}/lifestyle", headers=acc.h, json={"date": y, "sleep_hours": 8, "activity_minutes": 60, "stress_level": 2})
    assert (await client.put(f"{API}/lifestyle/{b.json()['id']}", headers=acc.h,
                             json={"date": today.isoformat()})).status_code == 409
    s = (await client.get(f"{API}/lifestyle/summary", headers=acc.h, params={"days": 7})).json()
    assert s["n_entries"] == 2 and s["avg_sleep_hours"] == 7.0 and s["avg_activity_minutes"] == 45.0 and s["avg_stress"] == 3.0
    for bad in ({"date": "2026-01-01", "sleep_hours": 25}, {"date": "2026-01-01", "sleep_hours": -1},
                {"date": "2026-01-01", "stress_level": 6}, {"date": "2026-01-01", "water_ml": -5},
                {"date": (today + timedelta(days=9)).isoformat()}):
        assert (await client.post(f"{API}/lifestyle", headers=acc.h, json=bad)).status_code == 400, bad


async def test_empty_summary(client):
    acc = await signup(client)
    s = (await client.get(f"{API}/lifestyle/summary", headers=acc.h)).json()
    assert s["n_entries"] == 0 and s["avg_sleep_hours"] is None


async def test_mood_records(client):
    acc = await signup(client)
    r = await client.post(f"{API}/mood", headers=acc.h, json={
        "logged_at": "2026-03-01T20:00:00+00:00", "mood_score": 4, "tags": [" Calm ", "", "FOCUSED"]})
    assert r.status_code == 201 and r.json()["tags"] == ["calm", "focused"]
    for bad in ({"logged_at": "2026-03-01T20:00:00+00:00", "mood_score": 9},
                {"logged_at": "2026-03-01T20:00:00+00:00", "mood_score": 3, "tags": ["x" * 40]}):
        assert (await client.post(f"{API}/mood", headers=acc.h, json=bad)).status_code == 400
    assert len((await client.get(f"{API}/mood", headers=acc.h)).json()) == 1


async def test_free_text_is_encrypted_at_rest(client, sessionmaker_):
    acc = await signup(client)
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01", notes="very private cycle note"))
    await client.post(f"{API}/lifestyle", headers=acc.h, json={"date": "2026-01-01", "nutrition_notes": "ate lots of paneer"})
    async with sessionmaker_() as s:
        n1 = (await s.execute(text("select notes from cycle_records"))).scalar_one()
        n2 = (await s.execute(text("select nutrition_notes from lifestyle_records"))).scalar_one()
    assert n1.startswith("k1:") and "private" not in n1
    assert n2.startswith("k1:") and "paneer" not in n2
    assert (await client.get(f"{API}/cycles", headers=acc.h)).json()[0]["notes"] == "very private cycle note"


async def test_timeline_events_follow_record_lifecycle(client, sessionmaker_):
    acc = await signup(client)

    async def rows():
        async with sessionmaker_() as s:
            return (await s.execute(text("select kind, source_table, payload from timeline_events order by kind"))).all()

    c = (await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01", "2026-01-04", notes="secret"))).json()
    await client.post(f"{API}/symptoms", headers=acc.h, json={
        "logged_at": "2026-01-02T08:00:00+00:00", "symptom_code": "headache", "severity": 2})
    await client.post(f"{API}/lifestyle", headers=acc.h, json={"date": "2026-01-02", "sleep_hours": 7.5})
    await client.post(f"{API}/mood", headers=acc.h, json={"logged_at": "2026-01-02T20:00:00+00:00", "mood_score": 3})
    got = await rows()
    assert [r[0] for r in got] == ["cycle", "lifestyle", "mood", "symptom"]
    assert all("secret" not in str(r[2]) for r in got)  # encrypted free text never leaks into the read model
    await client.put(f"{API}/cycles/{c['id']}", headers=acc.h, json=cyc("2026-01-01", "2026-01-06"))
    cycle_row = next(r for r in await rows() if r[0] == "cycle")
    assert cycle_row[2]["end_date"] == "2026-01-06"
    await client.delete(f"{API}/cycles/{c['id']}", headers=acc.h)
    assert [r[0] for r in await rows()] == ["lifestyle", "mood", "symptom"]


async def test_failed_write_leaves_no_partial_state(client, sessionmaker_):
    acc = await signup(client)
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01"))
    await client.post(f"{API}/cycles", headers=acc.h, json=cyc("2026-01-01"))  # 409
    async with sessionmaker_() as s:
        assert (await s.execute(text("select count(*) from cycle_records"))).scalar_one() == 1
        assert (await s.execute(text("select count(*) from timeline_events"))).scalar_one() == 1


async def test_db_constraints_hold_even_if_api_is_bypassed(sessionmaker_, client):
    acc = await signup(client)
    from sqlalchemy.exc import IntegrityError
    async with sessionmaker_() as s:
        with pytest.raises(IntegrityError):
            await s.execute(text("insert into mood_records (user_id, logged_at, mood_score) values (:u, now(), 9)"),
                            {"u": acc.user_id})
        await s.rollback()
        with pytest.raises(IntegrityError):
            await s.execute(text("insert into cycle_records (user_id, start_date, end_date) values (:u, '2026-02-02', '2026-01-01')"),
                            {"u": acc.user_id})
