import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';

import { tokenStore } from '@/auth/tokenStore';
import { API_BASE_URL, REQUEST_TIMEOUT_MS } from '@/config';
import type { TokenPair } from '@/types/api';

import { toApiError } from './errors';

/** Endpoints that must never carry a Bearer token or trigger a refresh-and-retry. */
const PUBLIC_PATHS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/forgot-password', '/auth/reset-password'];
const isPublic = (url?: string): boolean => PUBLIC_PATHS.some((p) => url?.startsWith(p));

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

let accessToken: string | null = null;
let onSessionExpired: (() => void) | null = null;

export const session = {
  setAccessToken: (t: string | null): void => { accessToken = t; },
  getAccessToken: (): string | null => accessToken,
  /** Called when the refresh token is rejected: the user must sign in again. */
  setExpiredHandler: (fn: (() => void) | null): void => { onSessionExpired = fn; },
};

export function createApiClient(
  baseURL: string = API_BASE_URL,
  // A bare instance (no interceptors) for the refresh call itself, so it can never recurse. Injectable for tests.
  bare: AxiosInstance = axios.create({ baseURL, timeout: REQUEST_TIMEOUT_MS }),
): AxiosInstance {
  const client = axios.create({ baseURL, timeout: REQUEST_TIMEOUT_MS, headers: { Accept: 'application/json' } });
  let inFlight: Promise<string> | null = null;

  async function refreshAccessToken(): Promise<string> {
    const refresh = await tokenStore.getRefreshToken();
    if (!refresh) throw toApiError({ isAxiosError: true, response: { status: 401, data: {} } });
    const { data } = await bare.post<TokenPair>('/auth/refresh', { refresh_token: refresh });
    await tokenStore.setRefreshToken(data.refresh_token); // rotation: the old token is now dead
    accessToken = data.access_token;
    return data.access_token;
  }

  client.interceptors.request.use((config) => {
    if (accessToken && !isPublic(config.url)) config.headers.set('Authorization', `Bearer ${accessToken}`);
    return config;
  });

  client.interceptors.response.use(
    (r) => r,
    async (error: unknown) => {
      const apiErr = toApiError(error);
      const original = (axios.isAxiosError(error) ? error.config : undefined) as RetriableConfig | undefined;
      if (apiErr.status !== 401 || !original || original._retried || isPublic(original.url)) throw apiErr;
      original._retried = true;
      try {
        // Single-flight: concurrent 401s share one refresh (refresh tokens are single-use).
        inFlight ??= refreshAccessToken().finally(() => { inFlight = null; });
        const token = await inFlight;
        original.headers.set('Authorization', `Bearer ${token}`);
        return await client.request(original);
      } catch (refreshErr) {
        const e = toApiError(refreshErr);
        if (e.status === 401) {
          // Refresh token rejected (expired, revoked, or reuse detected): end the session.
          accessToken = null;
          await tokenStore.clear().catch(() => undefined);
          onSessionExpired?.();
        }
        throw e; // network errors keep the session: the user is just offline
      }
    },
  );
  return client;
}

export const api = createApiClient();

/** Used by AuthContext for the initial silent sign-in at app start. */
export async function refreshSession(baseURL: string = API_BASE_URL): Promise<TokenPair> {
  const refresh = await tokenStore.getRefreshToken();
  if (!refresh) throw toApiError({ isAxiosError: true, response: { status: 401, data: {} } });
  try {
    const { data } = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token: refresh }, { timeout: REQUEST_TIMEOUT_MS });
    await tokenStore.setRefreshToken(data.refresh_token);
    accessToken = data.access_token;
    return data;
  } catch (e) {
    throw toApiError(e);
  }
}
