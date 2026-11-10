import AsyncStorage from '@react-native-async-storage/async-storage';
import { DarkTheme as NavDark, DefaultTheme as NavLight, type Theme as NavTheme } from '@react-navigation/native';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';
import { MD3DarkTheme, MD3LightTheme, PaperProvider, type MD3Theme } from 'react-native-paper';

import { darkColors, lightColors, type AppColors } from './colors';

export type ThemePreference = 'system' | 'light' | 'dark';
const STORAGE_KEY = 'pref.theme';

export type AppTheme = MD3Theme & { colors: MD3Theme['colors'] & Pick<AppColors, 'period' | 'onPeriod'> };

export function buildTheme(dark: boolean): AppTheme {
  const base = dark ? MD3DarkTheme : MD3LightTheme;
  const c = dark ? darkColors : lightColors;
  return { ...base, roundness: 4, colors: { ...base.colors, ...c } } as AppTheme;
}

export function buildNavTheme(theme: AppTheme, dark: boolean): NavTheme {
  const base = dark ? NavDark : NavLight;
  return {
    ...base, dark,
    colors: { primary: theme.colors.primary, background: theme.colors.background, card: theme.colors.surface,
      text: theme.colors.onSurface, border: theme.colors.outlineVariant, notification: theme.colors.tertiary },
  };
}

type Ctx = { preference: ThemePreference; setPreference: (p: ThemePreference) => void; dark: boolean; theme: AppTheme; navTheme: NavTheme };
const ThemeCtx = createContext<Ctx | null>(null);

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [preference, setPref] = useState<ThemePreference>('system');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((v) => { if (v === 'light' || v === 'dark' || v === 'system') setPref(v); })
      .catch(() => undefined);
  }, []);

  const setPreference = useCallback((p: ThemePreference) => {
    setPref(p);
    AsyncStorage.setItem(STORAGE_KEY, p).catch(() => undefined);
  }, []);

  const dark = preference === 'system' ? system === 'dark' : preference === 'dark';
  const value = useMemo(() => {
    const theme = buildTheme(dark);
    return { preference, setPreference, dark, theme, navTheme: buildNavTheme(theme, dark) };
  }, [preference, setPreference, dark]);

  return (
    <ThemeCtx.Provider value={value}>
      <PaperProvider theme={value.theme}>{children}</PaperProvider>
    </ThemeCtx.Provider>
  );
}

export function useAppTheme(): Ctx {
  const v = useContext(ThemeCtx);
  if (!v) throw new Error('useAppTheme must be used inside AppThemeProvider');
  return v;
}
