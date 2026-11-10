import type { ExpoConfig } from 'expo/config';

// Public, build-time values only. NEVER put secrets here: everything in the app bundle is readable.
const config: ExpoConfig = {
  name: 'Wellness',
  slug: 'womens-wellness',
  version: '0.3.0',
  orientation: 'portrait',
  scheme: 'wellness',
  userInterfaceStyle: 'automatic',
  ios: { supportsTablet: false, bundleIdentifier: 'com.example.wellness' },
  android: { package: 'com.example.wellness' },
  plugins: ['expo-secure-store'],
  extra: { apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/v1' },
};

export default config;
