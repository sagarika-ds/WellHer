import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Alert, Share, View } from 'react-native';
import { Button, Divider, List, SegmentedButtons, Text } from 'react-native-paper';
import type { z } from 'zod';

import { endpoints } from '@/api/endpoints';
import { errorMessage } from '@/api/errors';
import { useAccessHistory, useAISettings, useConsents, useProfile, useSaveAISettings, useSaveProfile, useSetConsent } from '@/api/hooks';
import { useAuth } from '@/auth/AuthContext';
import { DateField, SwitchRow, TextField } from '@/components/forms';
import { EmptyState, ErrorState, FormError, InfoCard, Loading, Screen, Section } from '@/components/ui';
import { DISCLAIMER } from '@/config';
import { useRootNav } from '@/navigation/hooks';
import type { RootParamList } from '@/navigation/types';
import { useAppTheme, type ThemePreference } from '@/theme';
import { CONSENT_PURPOSES, type ConsentPurpose } from '@/types/api';
import { prettyDateTime } from '@/utils/dates';
import { deleteAccountSchema, profileSchema, splitList } from '@/utils/validation';

export function MeScreen() {
  const nav = useRootNav();
  const { user, logout } = useAuth();
  const { preference, setPreference } = useAppTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportData = async () => {
    setBusy(true); setError(null);
    try {
      const out = await endpoints.exportData();
      await Share.share({ title: 'My wellness data', message: JSON.stringify(out.data, null, 2) });
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  };

  return (
    <Screen>
      <InfoCard tone="soft">
        <Text variant="titleLarge" accessibilityRole="header">{user?.display_name}</Text>
        <Text>{user?.email}</Text>
      </InfoCard>
      <Section title="Account">
        <InfoCard>
          <List.Item title="Health profile" left={(p) => <List.Icon {...p} icon="account-outline" />} onPress={() => nav.navigate('ProfileEdit')} />
          <Divider />
          <List.Item title="Privacy and consent" left={(p) => <List.Icon {...p} icon="shield-lock-outline" />} onPress={() => nav.navigate('Consents')} />
          <Divider />
          <List.Item title="AI and data sharing" left={(p) => <List.Icon {...p} icon="robot-outline" />} onPress={() => nav.navigate('AISettings')} />
          <Divider />
          <List.Item title="Who accessed my data" left={(p) => <List.Icon {...p} icon="history" />} onPress={() => nav.navigate('AccessHistory')} />
        </InfoCard>
      </Section>
      <Section title="Appearance">
        <SegmentedButtons value={preference} onValueChange={(v) => setPreference(v as ThemePreference)}
          buttons={[{ value: 'system', label: 'System' }, { value: 'light', label: 'Light' }, { value: 'dark', label: 'Dark' }]} />
      </Section>
      <Section title="Your data">
        <FormError error={error ? new Error(error) : null} />
        <Button mode="outlined" icon="export-variant" onPress={() => void exportData()} loading={busy} disabled={busy}>Export my data</Button>
        <Button mode="outlined" icon="delete-outline" textColor="#B3261E" onPress={() => nav.navigate('DeleteAccount')}>Delete my account</Button>
      </Section>
      <Button mode="contained-tonal" icon="logout" onPress={() => void logout()}>Sign out</Button>
      <Text variant="bodySmall">{DISCLAIMER}</Text>
      <Text variant="bodySmall">Version 0.3.0</Text>
    </Screen>
  );
}

type ProfileValues = z.input<typeof profileSchema>;
export function ProfileEditScreen({ navigation }: NativeStackScreenProps<RootParamList, 'ProfileEdit'>) {
  const profile = useProfile();
  const save = useSaveProfile();
  const { control, handleSubmit, reset } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema) as never,
    defaultValues: { date_of_birth: '', conditions: '', dietary_prefs: '', goals: '' },
  });
  useEffect(() => {
    const p = profile.data;
    if (p) reset({ date_of_birth: p.date_of_birth ?? '', height_cm: p.height_cm ?? undefined, weight_kg: p.weight_kg ?? undefined, typical_cycle_length: p.typical_cycle_length ?? undefined,
      activity_level: (p.activity_level ?? undefined) as ProfileValues['activity_level'], conditions: (p.conditions_self_reported ?? []).join(', '), dietary_prefs: (p.dietary_prefs ?? []).join(', '), goals: (p.goals ?? []).join(', ') });
  }, [profile.data, reset]);
  const submit = handleSubmit(async (raw) => {
    const v = profileSchema.parse(raw);
    try {
      await save.mutateAsync({ date_of_birth: v.date_of_birth || null, height_cm: v.height_cm ?? null, weight_kg: v.weight_kg ?? null, typical_cycle_length: v.typical_cycle_length ?? null,
        activity_level: v.activity_level ?? null, conditions_self_reported: splitList(v.conditions), dietary_prefs: splitList(v.dietary_prefs), goals: splitList(v.goals) });
      navigation.goBack();
    } catch { /* shown below */ }
  });
  if (profile.isLoading) return <Loading />;
  if (profile.error) return <ErrorState error={profile.error} onRetry={() => void profile.refetch()} />;
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">Health profile</Text>
      <Text variant="bodySmall">Everything here is optional. Sensitive fields are stored encrypted.</Text>
      <DateField control={control} name="date_of_birth" label="Date of birth" optional maximumDate={new Date()} />
      <TextField control={control} name="height_cm" label="Height (cm)" keyboardType="decimal-pad" />
      <TextField control={control} name="weight_kg" label="Weight (kg)" keyboardType="decimal-pad" />
      <TextField control={control} name="typical_cycle_length" label="Typical cycle length (days)" keyboardType="numeric" />
      <Controller control={control} name="activity_level" render={({ field }) => (
        <View style={{ gap: 4 }}>
          <Text variant="labelLarge">Activity level</Text>
          <SegmentedButtons value={field.value ?? ''} onValueChange={(v) => field.onChange(v === field.value ? undefined : v)}
            buttons={['sedentary', 'light', 'moderate', 'active'].map((v) => ({ value: v, label: v }))} />
        </View>
      )} />
      <TextField control={control} name="conditions" label="Conditions you want to note" hint="Comma-separated, optional. Stored encrypted." />
      <TextField control={control} name="dietary_prefs" label="Dietary preferences" hint="Comma-separated, e.g. vegetarian, low sugar" />
      <TextField control={control} name="goals" label="Goals" hint="Comma-separated, e.g. sleep better" />
      <FormError error={save.error} />
      <Button mode="contained" onPress={() => void submit()} loading={save.isPending} disabled={save.isPending}>Save</Button>
    </Screen>
  );
}

const CONSENT_TEXT: Record<ConsentPurpose, { label: string; description: string }> = {
  health_tracking: { label: 'Health tracking', description: 'Store and show the cycles, symptoms, sleep and mood you log. Turning this off hides your tracking screens; your data is kept until you delete it.' },
  ml_processing: { label: 'Insights from my records', description: 'Allow analysis of your records to produce insights. Insight features arrive in a later version.' },
  llm_external: { label: 'External AI providers', description: 'Allow de-identified text to be sent to an outside AI service. Off unless you choose it.' },
  analytics: { label: 'Anonymous usage statistics', description: 'Never includes your health records.' },
};

export function ConsentsScreen() {
  const consents = useConsents();
  const set = useSetConsent();
  if (consents.isLoading) return <Loading />;
  if (consents.error) return <ErrorState error={consents.error} onRetry={() => void consents.refetch()} />;
  return (
    <Screen>
      <Text variant="bodyMedium">You decide what the app may do. Changes take effect immediately and are recorded in your access history.</Text>
      <FormError error={set.error} />
      <InfoCard>
        {CONSENT_PURPOSES.map((p) => {
          const c = consents.data?.find((x) => x.purpose === p);
          return (
            <View key={p}>
              <SwitchRow label={CONSENT_TEXT[p].label} description={`${CONSENT_TEXT[p].description}${c?.granted && c.granted_at ? ` Granted ${prettyDateTime(c.granted_at)}.` : ''}`}
                value={!!c?.granted} disabled={set.isPending} testID={`consent-${p}`} onValueChange={(granted) => set.mutate({ purpose: p, granted })} />
            </View>
          );
        })}
      </InfoCard>
    </Screen>
  );
}

const CONTEXT_LABELS: Record<string, string> = {
  cycle_summary: 'Cycle summary', symptom_summary: 'Symptom summary', lifestyle_summary: 'Sleep and lifestyle summary',
  mood_summary: 'Mood summary', patterns: 'Detected patterns', deviations: 'Changes from my usual', preferences: 'My preferences',
};

export function AISettingsScreen({ navigation }: NativeStackScreenProps<RootParamList, 'AISettings'>) {
  const settings = useAISettings();
  const consents = useConsents();
  const save = useSaveAISettings();
  type Draft = { personalization_enabled: boolean; external_llm_allowed: boolean; context_allowlist: string[]; chat_retention_days: number };
  const [edits, setEdits] = useState<Partial<Draft>>({});
  const draft: Draft | null = settings.data ? { ...settings.data, ...edits } : null;
  const patch = (p: Partial<Draft>) => setEdits((e) => ({ ...e, ...p }));
  if (settings.isLoading || consents.isLoading || !draft) return settings.error ? <ErrorState error={settings.error} onRetry={() => void settings.refetch()} /> : <Loading />;
  const externalConsent = !!consents.data?.find((c) => c.purpose === 'llm_external')?.granted;
  const toggleKey = (k: string) => patch({ context_allowlist: draft.context_allowlist.includes(k) ? draft.context_allowlist.filter((x) => x !== k) : [...draft.context_allowlist, k] });
  const submit = async () => {
    try { await save.mutateAsync(draft as never); navigation.goBack(); } catch { /* shown below */ }
  };
  return (
    <Screen>
      <Text variant="bodyMedium">Controls which of your information an AI assistant may use. AI features arrive in a later version; these choices are enforced on the server from day one.</Text>
      <InfoCard>
        <SwitchRow label="Personalization" description="Use preferences you approve to tailor responses." value={draft.personalization_enabled} onValueChange={(v) => patch({ personalization_enabled: v })} testID="ai-personalization" />
        <SwitchRow label="Allow external AI providers" description={externalConsent ? 'De-identified text may be sent to an outside AI service.' : 'Requires the "External AI providers" consent first (Privacy and consent).'}
          value={draft.external_llm_allowed} disabled={!externalConsent} onValueChange={(v) => patch({ external_llm_allowed: v })} testID="ai-external" />
      </InfoCard>
      <Section title="What an assistant may see">
        <InfoCard>
          {Object.entries(CONTEXT_LABELS).map(([k, l]) => (
            <SwitchRow key={k} label={l} value={draft.context_allowlist.includes(k)} onValueChange={() => toggleKey(k)} testID={`ctx-${k}`} />
          ))}
        </InfoCard>
      </Section>
      <Section title="Keep chat history">
        <SegmentedButtons value={String(draft.chat_retention_days)} onValueChange={(v) => patch({ chat_retention_days: Number(v) })}
          buttons={[{ value: '0', label: 'None' }, { value: '7', label: '7 d' }, { value: '30', label: '30 d' }, { value: '90', label: '90 d' }]} />
      </Section>
      <FormError error={save.error} />
      <Button mode="contained" onPress={() => void submit()} loading={save.isPending} disabled={save.isPending}>Save</Button>
    </Screen>
  );
}

export function AccessHistoryScreen() {
  const history = useAccessHistory();
  if (history.isLoading) return <Loading />;
  if (history.error) return <ErrorState error={history.error} onRetry={() => void history.refetch()} />;
  return (
    <Screen onRefresh={() => void history.refetch()} refreshing={history.isRefetching}>
      <Text variant="bodyMedium">A record of sign-ins and of every time your data was read, changed, exported or sent for processing.</Text>
      {history.data && history.data.length > 0 ? (
        <InfoCard>
          {history.data.map((h, i) => (
            <List.Item key={`${h.timestamp}-${i}`} title={`${h.action.replace(/_/g, ' ')}${h.resource ? ` · ${h.resource.replace(/_/g, ' ')}` : ''}`}
              description={`${prettyDateTime(h.timestamp)}${h.outcome !== 'success' ? ` · ${h.outcome}` : ''}`} />
          ))}
        </InfoCard>
      ) : <EmptyState title="Nothing recorded yet" />}
    </Screen>
  );
}

type DeleteValues = z.infer<typeof deleteAccountSchema>;
export function DeleteAccountScreen() {
  const { logout } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<DeleteValues>({ resolver: zodResolver(deleteAccountSchema), defaultValues: { password: '', confirm: '' as never } });
  const submit = handleSubmit((v) => {
    Alert.alert('Delete everything?', 'Your account and all your records will be permanently erased. This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete forever', style: 'destructive', onPress: () => {
        setError(null);
        endpoints.deleteAccount(v.password).then(() => logout()).catch((e: unknown) => setError(errorMessage(e)));
      } },
    ]);
  });
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">Delete my account</Text>
      <Text>This permanently erases your account, your health records and your settings. Export your data first if you want a copy.</Text>
      <TextField control={control} name="password" label="Your password" secure autoComplete="password" />
      <TextField control={control} name="confirm" label="Type DELETE to confirm" />
      {error ? <FormError error={new Error(error)} /> : null}
      <Button mode="contained" buttonColor="#B3261E" textColor="#FFFFFF" onPress={() => void submit()} loading={isSubmitting} disabled={isSubmitting}>Delete my account</Button>
    </Screen>
  );
}
