import Constants from 'expo-constants';

const fromExtra = (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)?.apiBaseUrl;

/** Public API base URL (build-time). Defaults target the Android emulator's route to the host machine. */
export const API_BASE_URL: string = (process.env.EXPO_PUBLIC_API_BASE_URL ?? fromExtra ?? 'http://10.0.2.2:8000/api/v1').replace(/\/+$/, '');

export const REQUEST_TIMEOUT_MS = 15_000;

export const DISCLAIMER =
  'This app supports wellness tracking and health awareness. It does not diagnose, treat or replace advice from a qualified healthcare professional.';
