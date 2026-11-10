import { QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react-native';
import React from 'react';

import { ApiError } from '@/api/errors';
import { newQueryClient } from '@/__tests__/testUtils';

import { AuthProvider, useAuth } from './AuthContext';
import { tokenStore } from './tokenStore';

jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
jest.mock('@/api/client', () => ({
  session: { setAccessToken: jest.fn(), setExpiredHandler: jest.fn(), getAccessToken: jest.fn() },
  refreshSession: jest.fn(), api: {},
}));

import { endpoints, type Endpoints } from '@/api/endpoints';
import { refreshSession, session } from '@/api/client';

const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;
const refresh = refreshSession as jest.Mock;
const sess = session as unknown as Record<'setAccessToken' | 'setExpiredHandler' | 'getAccessToken', jest.Mock>;
const USER = { id: 'u1', email: 'a@b.co', display_name: 'Asha', role: 'user' };

const setup = async () => {
  const qc = newQueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => <QueryClientProvider client={qc}><AuthProvider>{children}</AuthProvider></QueryClientProvider>;
  const rendered = await renderHook(() => useAuth(), { wrapper });
  return { qc, ...rendered };
};

beforeEach(async () => { jest.clearAllMocks(); await tokenStore.clear(); });

it('starts signed out when there is no stored session', async () => {
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedOut'));
  expect(refresh).not.toHaveBeenCalled();
});

it('restores the session silently from the stored refresh token', async () => {
  await tokenStore.setRefreshToken('stored');
  refresh.mockResolvedValue({}); ep.me.mockResolvedValue(USER);
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedIn'));
  expect(result.current.user).toEqual(USER);
});

it('signs out and wipes the token when the stored refresh token is rejected', async () => {
  await tokenStore.setRefreshToken('revoked');
  refresh.mockRejectedValue(new ApiError(401, 'unauthenticated', 'Invalid refresh token.'));
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedOut'));
  expect(await tokenStore.getRefreshToken()).toBeNull();
});

it('offline at start: keeps the stored session and offers retry', async () => {
  await tokenStore.setRefreshToken('stored');
  refresh.mockRejectedValueOnce(new ApiError(0, 'network_error', 'offline'));
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('unreachable'));
  expect(await tokenStore.getRefreshToken()).toBe('stored');
  refresh.mockResolvedValue({}); ep.me.mockResolvedValue(USER);
  await act(async () => result.current.retryBootstrap());
  await waitFor(() => expect(result.current.status).toBe('signedIn'));
});

it('login keeps the access token in memory and persists only the refresh token', async () => {
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedOut'));
  ep.login.mockResolvedValue({ access_token: 'A', refresh_token: 'R', expires_in: 900 }); ep.me.mockResolvedValue(USER);
  await act(async () => result.current.login('  a@b.co ', 'pw'));
  expect(ep.login).toHaveBeenCalledWith('a@b.co', 'pw', 'mobile');
  expect(sess.setAccessToken).toHaveBeenCalledWith('A');
  expect(await tokenStore.getRefreshToken()).toBe('R');
  expect(result.current.status).toBe('signedIn');
});

it('failed login leaves the user signed out and surfaces the error', async () => {
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedOut'));
  ep.login.mockRejectedValue(new ApiError(401, 'unauthenticated', 'Invalid email or password.'));
  await expect(act(async () => result.current.login('a@b.co', 'bad'))).rejects.toThrow('Invalid email or password.');
  expect(result.current.status).toBe('signedOut');
  expect(await tokenStore.getRefreshToken()).toBeNull();
});

it('register sends trimmed fields and the explicit consent choices, then signs in', async () => {
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedOut'));
  ep.register.mockResolvedValue(USER); ep.login.mockResolvedValue({ access_token: 'A', refresh_token: 'R', expires_in: 900 }); ep.me.mockResolvedValue(USER);
  const consents = [{ purpose: 'health_tracking' as const, granted: true }, { purpose: 'analytics' as const, granted: false }];
  await act(async () => result.current.register({ email: ' a@b.co ', password: 'pw', displayName: ' Asha ', consents }));
  expect(ep.register).toHaveBeenCalledWith({ email: 'a@b.co', password: 'pw', display_name: 'Asha', consents });
  expect(result.current.status).toBe('signedIn');
});

it('logout ends the session even if the server call fails, and clears cached health data', async () => {
  await tokenStore.setRefreshToken('stored'); refresh.mockResolvedValue({}); ep.me.mockResolvedValue(USER);
  const { result, qc } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedIn'));
  qc.setQueryData(['cycles'], [{ id: 'secret' }]);
  ep.logout.mockRejectedValue(new ApiError(0, 'network_error', 'offline'));
  await act(async () => result.current.logout());
  expect(result.current.status).toBe('signedOut');
  expect(await tokenStore.getRefreshToken()).toBeNull();
  expect(qc.getQueryData(['cycles'])).toBeUndefined();
  expect(sess.setAccessToken).toHaveBeenLastCalledWith(null);
});

it('a server-side session end (refresh rejected mid-use) signs the user out', async () => {
  await tokenStore.setRefreshToken('stored'); refresh.mockResolvedValue({}); ep.me.mockResolvedValue(USER);
  const { result } = await setup();
  await waitFor(() => expect(result.current.status).toBe('signedIn'));
  const onExpired = sess.setExpiredHandler.mock.calls.map((c) => c[0]).filter(Boolean).pop() as () => void;
  await act(async () => onExpired());
  expect(result.current.status).toBe('signedOut');
  expect(result.current.user).toBeNull();
});
