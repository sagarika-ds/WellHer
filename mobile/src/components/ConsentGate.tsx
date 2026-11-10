import React from 'react';
import { Button, Text } from 'react-native-paper';

import { useSetConsent } from '@/api/hooks';
import { toApiError } from '@/api/errors';

import { FormError, InfoCard } from './ui';

/**
 * Wraps health content. If the server answered `consent_required`, explains why and offers to grant the
 * consent; otherwise renders its children. The decision comes from the server, never from a local guess.
 */
export function ConsentGate({ error, children }: { error: unknown; children: React.ReactNode }) {
  const setConsent = useSetConsent();
  if (!error || !toApiError(error).isConsentRequired) return <>{children}</>;
  return (
    <InfoCard tone="soft">
      <Text variant="titleMedium" accessibilityRole="header">Health tracking is turned off</Text>
      <Text variant="bodyMedium">
        To store and view the cycles, symptoms, sleep and mood you log, we need your permission. Nothing is saved
        until you agree, and you can withdraw it at any time in Privacy settings.
      </Text>
      <FormError error={setConsent.error} />
      <Button mode="contained" loading={setConsent.isPending} disabled={setConsent.isPending}
        onPress={() => setConsent.mutate({ purpose: 'health_tracking', granted: true })}>
        Turn on health tracking
      </Button>
    </InfoCard>
  );
}
