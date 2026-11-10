import AsyncStorage from '@react-native-async-storage/async-storage';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useMemo, useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { createQueryClient } from '@/api/queryClient';
import { AuthProvider } from '@/auth/AuthContext';
import { RootNavigator } from '@/navigation/RootNavigator';
import { AppThemeProvider, useAppTheme } from '@/theme';

const ONBOARDING_KEY = 'onboarding.done';

function Shell() {
  const { navTheme, dark } = useAppTheme();
  const [loaded, setLoaded] = useState(false);
  const [done, setDone] = useState(false);
  useEffect(() => {
    AsyncStorage.getItem(ONBOARDING_KEY).then((v) => setDone(v === '1')).catch(() => undefined).finally(() => setLoaded(true));
  }, []);
  if (!loaded) return null;
  return (
    <NavigationContainer theme={navTheme}>
      <RootNavigator onboardingDone={done} onFinishOnboarding={() => { setDone(true); AsyncStorage.setItem(ONBOARDING_KEY, '1').catch(() => undefined); }} />
      <StatusBar style={dark ? 'light' : 'dark'} />
    </NavigationContainer>
  );
}

export default function App() {
  const queryClient = useMemo(() => createQueryClient(), []);
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AppThemeProvider>
          <AuthProvider>
            <Shell />
          </AuthProvider>
        </AppThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
