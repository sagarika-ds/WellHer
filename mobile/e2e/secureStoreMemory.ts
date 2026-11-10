// In-memory stand-in for expo-secure-store (Node has no keychain). Same API surface the app uses.
const store = new Map<string, string>();
export const WHEN_UNLOCKED_THIS_DEVICE_ONLY = 'WHEN_UNLOCKED_THIS_DEVICE_ONLY';
export type SecureStoreOptions = Record<string, unknown>;
export const getItemAsync = async (k: string): Promise<string | null> => store.get(k) ?? null;
export const setItemAsync = async (k: string, v: string): Promise<void> => { store.set(k, v); };
export const deleteItemAsync = async (k: string): Promise<void> => { store.delete(k); };
