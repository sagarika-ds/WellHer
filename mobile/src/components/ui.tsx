import React from 'react';
import { RefreshControl, ScrollView, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { ActivityIndicator, Button, Card, Text, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ApiError, toApiError } from '@/api/errors';

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 } as const;

export function Screen({ children, scroll = true, style, onRefresh, refreshing = false }: {
  children: React.ReactNode; scroll?: boolean; style?: StyleProp<ViewStyle>; onRefresh?: () => void; refreshing?: boolean;
}) {
  const theme = useTheme();
  const inner = <View style={[styles.content, style]}>{children}</View>;
  return (
    <SafeAreaView edges={['left', 'right']} style={{ flex: 1, backgroundColor: theme.colors.background }}>
      {scroll ? (
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.scroll}
          refreshControl={onRefresh ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} /> : undefined}>{inner}</ScrollView>
      ) : inner}
    </SafeAreaView>
  );
}

export function Section({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHead}>
        <Text variant="titleMedium" accessibilityRole="header">{title}</Text>
        {action}
      </View>
      {children}
    </View>
  );
}

export function InfoCard({ children, tone = 'default' }: { children: React.ReactNode; tone?: 'default' | 'soft' }) {
  const theme = useTheme();
  return (
    <Card mode="contained" style={{ backgroundColor: tone === 'soft' ? theme.colors.primaryContainer : theme.colors.surface }}>
      <Card.Content style={{ gap: spacing.sm }}>{children}</Card.Content>
    </Card>
  );
}

export function Loading({ label = 'Loading' }: { label?: string }) {
  return <View style={styles.center} accessibilityRole="progressbar" accessibilityLabel={label}><ActivityIndicator /></View>;
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: React.ReactNode }) {
  return (
    <View style={styles.center}>
      <Text variant="titleMedium" style={styles.centerText}>{title}</Text>
      {hint ? <Text variant="bodyMedium" style={styles.centerText}>{hint}</Text> : null}
      {action}
    </View>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const e = toApiError(error);
  return (
    <View style={styles.center} accessibilityRole="alert">
      <Text variant="titleMedium" style={styles.centerText}>{e.isNetwork ? "You're offline" : 'Something went wrong'}</Text>
      <Text variant="bodyMedium" style={styles.centerText}>{e.message}</Text>
      {onRetry ? <Button mode="outlined" onPress={onRetry}>Try again</Button> : null}
    </View>
  );
}

export function FormError({ error }: { error: unknown }) {
  const theme = useTheme();
  if (!error) return null;
  return <Text accessibilityRole="alert" style={{ color: theme.colors.error }}>{error instanceof ApiError || error instanceof Error ? error.message : 'Something went wrong.'}</Text>;
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1 },
  content: { padding: spacing.md, gap: spacing.md },
  section: { gap: spacing.sm },
  sectionHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  center: { padding: spacing.lg, alignItems: 'center', gap: spacing.sm },
  centerText: { textAlign: 'center' },
});
