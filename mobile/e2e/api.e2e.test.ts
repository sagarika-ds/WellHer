/**
 * End-to-end check of the app's REAL API layer (axios client, silent token refresh, endpoint functions,
 * error normalisation) against a LIVE backend. Run via scripts/mobile_e2e.sh (starts PostgreSQL-backed backend).
 */
import axios from 'axios';

import { createApiClient, session } from '../src/api/client';
import { createEndpoints } from '../src/api/endpoints';
import { ApiError } from '../src/api/errors';
import { tokenStore } from '../src/auth/tokenStore';

const BASE = process.env.BACKEND_URL ?? '';
const PASSWORD = 'Violet-Harbor-Lamp-42';
const api = createApiClient(BASE);
const ep = createEndpoints(api);
const expired = jest.fn();
const email = `e2e-${Date.now()}@example.com`;
const today = new Date().toISOString().slice(0, 10);

async function signIn(addr: string) {
  const t = await ep.login(addr, PASSWORD, 'e2e');
  await tokenStore.setRefreshToken(t.refresh_token);
  session.setAccessToken(t.access_token);
  return t;
}
async function failure(p: Promise<unknown>): Promise<ApiError> {
  try { await p; } catch (e) { return e as ApiError; }
  throw new Error('expected the call to fail');
}

beforeAll(() => { if (!BASE) throw new Error('set BACKEND_URL (e.g. http://localhost:8766/api/v1)'); session.setExpiredHandler(expired); });

test('01 register WITHOUT consent: health data is refused with consent_required until granted', async () => {
  const user = await ep.register({ email, password: PASSWORD, display_name: 'E2E', consents: [{ purpose: 'analytics', granted: false }] });
  expect(user.email).toBe(email);
  await signIn(email);
  expect((await ep.me()).display_name).toBe('E2E');
  const err = await failure(ep.listCycles());
  expect(err).toBeInstanceOf(ApiError);
  expect([err.status, err.code, err.isConsentRequired]).toEqual([403, 'consent_required', true]);
  const granted = await ep.setConsent('health_tracking', true);
  expect(granted.granted).toBe(true);
  expect(await ep.listCycles()).toEqual([]);
});

test('02 records: create/list/update/stats/summary through the real endpoint functions', async () => {
  const c1 = await ep.createCycle({ start_date: '2026-01-01', end_date: '2026-01-05', flow_intensity: 3, notes: 'private' });
  await ep.createCycle({ start_date: '2026-01-29' });
  await ep.createCycle({ start_date: '2026-02-26' });
  expect(c1.notes).toBe('private');
  const stats = await ep.cycleStats();
  expect([stats.n_cycles, stats.mean_length, stats.min, stats.max]).toEqual([2, 28, 28, 28]);
  const listed = await ep.listCycles({ limit: 2 });
  expect(listed.map((c) => c.start_date)).toEqual(['2026-02-26', '2026-01-29']);
  await ep.updateCycle(c1.id, { start_date: '2026-01-01', end_date: '2026-01-06' });

  const s = await ep.createSymptom({ logged_at: new Date().toISOString(), symptom_code: 'headache', severity: 3 });
  expect(s.symptom_code).toBe('headache');
  const l = await ep.createLifestyle({ date: today, sleep_hours: 6.5, activity_minutes: 30, stress_level: 2 });
  const l2 = await ep.updateLifestyle(l.id, { date: today, sleep_hours: 7.5, activity_minutes: 30, stress_level: 2 });
  expect(l2.sleep_hours).toBe(7.5);
  await ep.createMood({ logged_at: new Date().toISOString(), mood_score: 4, tags: ['calm'] });
  const summary = await ep.lifestyleSummary(7);
  expect([summary.n_entries, summary.avg_sleep_hours]).toEqual([1, 7.5]);
  expect((await ep.listLifestyle({ date_from: today, date_to: today, limit: 1 })).map((x) => x.id)).toEqual([l.id]);
  expect((await ep.listMood({ limit: 5 }))[0]!.tags).toEqual(['calm']);
  await ep.deleteSymptom(s.id);
  expect(await ep.listSymptoms()).toEqual([]);
});

test('03 server errors arrive as normalised ApiErrors (validation 400, conflict 409, not found 404)', async () => {
  const bad = await failure(ep.createCycle({ start_date: '2026-03-10', end_date: '2026-03-01' }));
  expect([bad.status, bad.code]).toEqual([400, 'validation_error']);
  expect(bad.requestId).toBeTruthy();
  const dup = await failure(ep.createLifestyle({ date: today, sleep_hours: 5 }));
  expect([dup.status, dup.code]).toEqual([409, 'conflict']);
  const gone = await failure(ep.deleteCycle('00000000-0000-0000-0000-000000000000'));
  expect([gone.status, gone.code]).toEqual([404, 'not_found']);
});

test('04 an expired/invalid access token is refreshed silently, and the refresh token ROTATES', async () => {
  const before = await tokenStore.getRefreshToken();
  session.setAccessToken('not.a.valid.token');
  const cycles = await ep.listCycles();
  expect(cycles.length).toBe(3);
  const after = await tokenStore.getRefreshToken();
  expect(after).not.toBe(before);
  expect(session.getAccessToken()).not.toBe('not.a.valid.token');
  expect(expired).not.toHaveBeenCalled();
  // concurrent calls with a bad token share ONE refresh (single-use refresh tokens would otherwise kill the session)
  session.setAccessToken('still.not.valid');
  const r = await Promise.all([ep.listCycles(), ep.listMood(), ep.cycleStats(), ep.getProfile()]);
  expect(r).toHaveLength(4);
  expect(expired).not.toHaveBeenCalled();
});

test('05 replaying a rotated refresh token is detected by the server and ends the whole session', async () => {
  const stolen = (await tokenStore.getRefreshToken())!;
  await ep.listCycles(); // fine
  session.setAccessToken('bad.again.token');
  await ep.listCycles(); // rotates `stolen` away
  const replay = await failure(axios.post(`${BASE}/auth/refresh`, { refresh_token: stolen }).catch((e) => { throw e.response ? new ApiError(e.response.status, e.response.data.error.code, e.response.data.error.message) : e; }));
  expect(replay.status).toBe(401);
  // the legitimate client is now logged out too: its next refresh is rejected and the app is told to sign out
  session.setAccessToken('bad.once.more');
  const err = await failure(ep.listCycles());
  expect(err.status).toBe(401);
  expect(expired).toHaveBeenCalledTimes(1);
  expect(await tokenStore.getRefreshToken()).toBeNull();
});

test('06 privacy: AI settings gate, access history, export, and account erasure', async () => {
  await signIn(email);
  const ai = await ep.getAISettings();
  expect(ai.external_llm_allowed).toBe(false);
  const refused = await failure(ep.putAISettings({ ...ai, external_llm_allowed: true } as never));
  expect([refused.status, refused.code]).toEqual([403, 'consent_required']);
  await ep.setConsent('llm_external', true);
  expect((await ep.putAISettings({ ...ai, external_llm_allowed: true, context_allowlist: ['patterns' as const] })).context_allowlist).toEqual(['patterns']);
  const history = await ep.accessHistory(100, 0);
  expect(history.map((h) => h.action)).toEqual(expect.arrayContaining(['login', 'read', 'create', 'consent_granted', 'ai_settings_update']));
  const exp = await ep.exportData();
  expect(exp.data).toMatchObject({ user: { email }, cycles: expect.any(Array) });
  expect((exp.data as { cycles: unknown[] }).cycles).toHaveLength(3);
  await ep.deleteAccount(PASSWORD);
  const login = await failure(ep.login(email, PASSWORD));
  expect([login.status, login.message]).toEqual([401, 'Invalid email or password.']);
});
