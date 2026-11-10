import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react-native';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AppThemeProvider } from '@/theme';

export const newQueryClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity, staleTime: 0 }, mutations: { retry: false } } });

const METRICS = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };

export function Providers({ children, client }: { children: React.ReactNode; client?: QueryClient }) {
  const qc = React.useMemo(() => client ?? newQueryClient(), [client]);
  return (
    <SafeAreaProvider initialMetrics={METRICS}>
      <QueryClientProvider client={qc}>
        <AppThemeProvider>{children}</AppThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

export const renderWithProviders = (ui: React.ReactElement, client?: QueryClient) => render(<Providers client={client}>{ui}</Providers>);

export const navMock = () => ({ navigate: jest.fn(), goBack: jest.fn() });

/** Loosely-typed navigation props for rendering a screen in isolation. */
export const sp = (p: object) => p as { navigation: never; route: never };
