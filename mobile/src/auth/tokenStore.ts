import * as SecureStore from 'expo-secure-store';

/**
 * Only the REFRESH token is persisted, in the OS keychain/keystore (hardware-backed where available).
 * The short-lived access token lives in memory only (see api/client.ts), so it is never written to disk.
 */
const KEY = 'auth.refreshToken';
const OPTIONS: SecureStore.SecureStoreOptions = { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY };

export const tokenStore = {
  getRefreshToken: (): Promise<string | null> => SecureStore.getItemAsync(KEY, OPTIONS),
  setRefreshToken: (token: string): Promise<void> => SecureStore.setItemAsync(KEY, token, OPTIONS),
  clear: (): Promise<void> => SecureStore.deleteItemAsync(KEY, OPTIONS),
};
