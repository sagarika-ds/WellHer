import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import * as SecureStore from 'expo-secure-store';

import { tokenStore } from '@/auth/tokenStore';

import { createApiClient, session } from './client';
import { ApiError } from './errors';

const BASE = 'http://api.test';
let api: ReturnType<typeof createApiClient>;
let apiMock: MockAdapter;
let bareMock: MockAdapter;
let expired: jest.Mock;

beforeEach(async () => {
  const bare = axios.create({ baseURL: BASE });
  api = createApiClient(BASE, bare);
  apiMock = new MockAdapter(api);
  bareMock = new MockAdapter(bare);
  expired = jest.fn();
  session.setExpiredHandler(expired);
  session.setAccessToken('old-access');
  await tokenStore.setRefreshToken('old-refresh');
});
afterEach(() => { apiMock.restore(); bareMock.restore(); session.setAccessToken(null); session.setExpiredHandler(null); });

const authHeader = (req: { headers?: unknown }) => (req.headers as { get: (k: string) => unknown }).get('Authorization');

it('attaches the bearer token to protected calls only', async () => {
  const seen: Record<string, unknown> = {};
  apiMock.onGet('/cycles').reply((c) => { seen.protected = authHeader(c); return [200, []]; });
  apiMock.onPost('/auth/login').reply((c) => { seen.login = authHeader(c); return [200, {}]; });
  await api.get('/cycles');
  await api.post('/auth/login', {});
  expect(seen.protected).toBe('Bearer old-access');
  expect(seen.login).toBeUndefined();
});

it('on 401 refreshes silently, stores the ROTATED refresh token, and retries with the new access token', async () => {
  apiMock.onGet('/cycles').replyOnce(401, { error: { code: 'unauthenticated', message: 'expired' } });
  apiMock.onGet('/cycles').reply((c) => [authHeader(c) === 'Bearer new-access' ? 200 : 401, [{ id: 1 }]]);
  bareMock.onPost('/auth/refresh').reply(200, { access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 900 });
  const r = await api.get('/cycles');
  expect(r.data).toEqual([{ id: 1 }]);
  expect(JSON.parse(bareMock.history.post![0]!.data)).toEqual({ refresh_token: 'old-refresh' });
  expect(await tokenStore.getRefreshToken()).toBe('new-refresh');
  expect(session.getAccessToken()).toBe('new-access');
  expect(expired).not.toHaveBeenCalled();
});

it('shares ONE refresh between concurrent 401s (refresh tokens are single-use)', async () => {
  apiMock.onGet().reply((c) => [authHeader(c) === 'Bearer new-access' ? 200 : 401, {}]);
  bareMock.onPost('/auth/refresh').reply(async () => { await new Promise((r) => setTimeout(r, 20)); return [200, { access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 900 }]; });
  const res = await Promise.all([api.get('/cycles'), api.get('/symptoms'), api.get('/mood')]);
  expect(res.map((r) => r.status)).toEqual([200, 200, 200]);
  expect(bareMock.history.post).toHaveLength(1);
});

it('ends the session when the refresh token is rejected', async () => {
  apiMock.onGet('/cycles').reply(401, {});
  bareMock.onPost('/auth/refresh').reply(401, { error: { code: 'unauthenticated', message: 'Invalid refresh token.' } });
  await expect(api.get('/cycles')).rejects.toMatchObject({ status: 401 });
  expect(expired).toHaveBeenCalledTimes(1);
  expect(await tokenStore.getRefreshToken()).toBeNull();
  expect(session.getAccessToken()).toBeNull();
});

it('keeps the session when the refresh fails only because the network is down', async () => {
  apiMock.onGet('/cycles').reply(401, {});
  bareMock.onPost('/auth/refresh').networkError();
  await expect(api.get('/cycles')).rejects.toMatchObject({ code: 'network_error' });
  expect(expired).not.toHaveBeenCalled();
  expect(await tokenStore.getRefreshToken()).toBe('old-refresh');
});

it('does not loop: a retry that is still 401 fails after exactly one refresh', async () => {
  apiMock.onGet('/cycles').reply(401, {});
  bareMock.onPost('/auth/refresh').reply(200, { access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 900 });
  await expect(api.get('/cycles')).rejects.toBeInstanceOf(ApiError);
  expect(bareMock.history.post).toHaveLength(1);
});

it('never tries to refresh for a wrong password on login', async () => {
  apiMock.onPost('/auth/login').reply(401, { error: { code: 'unauthenticated', message: 'Invalid email or password.' } });
  await expect(api.post('/auth/login', {})).rejects.toMatchObject({ message: 'Invalid email or password.' });
  expect(bareMock.history.post).toHaveLength(0);
  expect(expired).not.toHaveBeenCalled();
});

it('returns normalised ApiError for other failures (consent, conflict, offline)', async () => {
  apiMock.onGet('/cycles').replyOnce(403, { error: { code: 'consent_required', message: 'm', request_id: 'rid' } });
  await expect(api.get('/cycles')).rejects.toMatchObject({ status: 403, isConsentRequired: true, requestId: 'rid' });
  apiMock.onGet('/cycles').networkErrorOnce();
  await expect(api.get('/cycles')).rejects.toMatchObject({ isNetwork: true });
});

it('only the refresh token is persisted, with device-only keychain access', async () => {
  expect(SecureStore.setItemAsync).toHaveBeenCalledWith('auth.refreshToken', 'old-refresh', { keychainAccessible: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY' });
  const keys = [...(SecureStore as unknown as { __store: Map<string, string> }).__store.keys()];
  expect(keys).toEqual(['auth.refreshToken']);
});
