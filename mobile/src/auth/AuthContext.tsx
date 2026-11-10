import { useQueryClient } from '@tanstack/react-query';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { session, refreshSession } from '@/api/client';
import { toApiError } from '@/api/errors';
import { endpoints } from '@/api/endpoints';
import type { ConsentChoice, UserOut } from '@/types/api';

import { tokenStore } from './tokenStore';

export type AuthStatus = 'loading' | 'signedOut' | 'signedIn' | 'unreachable';

type AuthCtx = {
  status: AuthStatus;
  user: UserOut | null;
  login: (email: string, password: string) => Promise<void>;
  register: (p: { email: string; password: string; displayName: string; consents: ConsentChoice[] }) => Promise<void>;
  logout: () => Promise<void>;
  retryBootstrap: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<UserOut | null>(null);

  const endSession = useCallback(() => {
    session.setAccessToken(null);
    setUser(null);
    qc.clear(); // never leave one user's cached health data in memory for the next
    setStatus('signedOut');
  }, [qc]);

  const bootstrap = useCallback(async () => {
    try {
      if (!(await tokenStore.getRefreshToken())) return endSession();
      await refreshSession();
      setUser(await endpoints.me());
      setStatus('signedIn');
    } catch (e) {
      const err = toApiError(e);
      if (err.isNetwork) return setStatus('unreachable'); // offline: keep the stored session, let the user retry
      await tokenStore.clear().catch(() => undefined);
      endSession();
    }
  }, [endSession]);

  useEffect(() => {
    session.setExpiredHandler(endSession);
    // Async start-up check: every setState inside bootstrap() runs after an await (initial state is already 'loading').
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void bootstrap();
    return () => session.setExpiredHandler(null);
  }, [bootstrap, endSession]);

  const login = useCallback(async (email: string, password: string) => {
    const t = await endpoints.login(email.trim(), password, 'mobile');
    await tokenStore.setRefreshToken(t.refresh_token);
    session.setAccessToken(t.access_token);
    setUser(await endpoints.me());
    setStatus('signedIn');
  }, []);

  const register = useCallback<AuthCtx['register']>(async ({ email, password, displayName, consents }) => {
    await endpoints.register({ email: email.trim(), password, display_name: displayName.trim(), consents });
    await login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    try { await endpoints.logout(); } catch { /* best effort: the local session is ended regardless */ }
    await tokenStore.clear().catch(() => undefined);
    endSession();
  }, [endSession]);

  const value = useMemo(() => ({ status, user, login, register, logout, retryBootstrap: () => { setStatus('loading'); void bootstrap(); } }),
    [status, user, login, register, logout, bootstrap]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useAuth must be used inside AuthProvider');
  return v;
}
