import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { Alert, View } from 'react-native';
import { Button, Chip, HelperText, List, Text } from 'react-native-paper';
import type { z } from 'zod';

import { toApiError } from '@/api/errors';
import { useCreateMood, useCreateSymptom, useDeleteSymptom, useLifestyle, useMood, useSaveLifestyle, useSymptoms } from '@/api/hooks';
import { ConsentGate } from '@/components/ConsentGate';
import { ChipsField, DateField, ScoreField, TextField } from '@/components/forms';
import { EmptyState, ErrorState, FormError, InfoCard, Loading, Screen, Section } from '@/components/ui';
import { useRootNav } from '@/navigation/hooks';
import type { RootParamList } from '@/navigation/types';
import { MOOD_TAGS, SYMPTOM_CODES } from '@/types/api';
import { nowISO, prettyDate, prettyDateTime, today } from '@/utils/dates';
import { lifestyleSchema, moodSchema, symptomSchema } from '@/utils/validation';

const label = (code: string) => code.replace(/_/g, ' ');

export function LogScreen() {
  const nav = useRootNav();
  const symptoms = useSymptoms({ limit: 10 });
  const lifestyle = useLifestyle({ limit: 7 });
  const mood = useMood({ limit: 7 });
  const del = useDeleteSymptom();
  const blockedErr = [symptoms, lifestyle, mood].find((q) => q.error)?.error;
  const confirmDelete = (id: string, name: string) =>
    Alert.alert('Delete this entry?', `${label(name)} will be removed.`, [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: () => del.mutate(id) }]);

  return (
    <Screen>
      <View style={{ gap: 8 }}>
        <Button mode="contained" icon="emoticon-sad-outline" onPress={() => nav.navigate('SymptomForm')}>Log a symptom</Button>
        <Button mode="contained-tonal" icon="sleep" onPress={() => nav.navigate('LifestyleForm')}>Log sleep and lifestyle</Button>
        <Button mode="contained-tonal" icon="emoticon-happy-outline" onPress={() => nav.navigate('MoodForm')}>Log mood</Button>
      </View>
      <ConsentGate error={blockedErr}>
        {[symptoms, lifestyle, mood].some((q) => q.isLoading) ? <Loading /> : null}
        {blockedErr && !toApiError(blockedErr).isConsentRequired ? <ErrorState error={blockedErr} onRetry={() => { void symptoms.refetch(); void lifestyle.refetch(); void mood.refetch(); }} /> : null}
        {!blockedErr && symptoms.data ? (
          <>
            <FormError error={del.error} />
            <Section title="Symptoms">
              {symptoms.data.length === 0 ? <EmptyState title="No symptoms logged" /> : (
                <InfoCard>
                  {symptoms.data.map((s) => (
                    <List.Item key={s.id} title={label(s.symptom_code)} description={`${prettyDateTime(s.logged_at)} · severity ${s.severity}/5`}
                      right={() => <Button onPress={() => confirmDelete(s.id, s.symptom_code)} accessibilityLabel={`Delete ${label(s.symptom_code)} entry`}>Delete</Button>} />
                  ))}
                </InfoCard>
              )}
            </Section>
            <Section title="Sleep and lifestyle">
              {(lifestyle.data ?? []).length === 0 ? <EmptyState title="No entries yet" /> : (
                <InfoCard>
                  {(lifestyle.data ?? []).map((l) => (
                    <List.Item key={l.id} title={prettyDate(l.date)}
                      description={[l.sleep_hours != null && `sleep ${l.sleep_hours} h`, l.activity_minutes != null && `activity ${l.activity_minutes} min`, l.stress_level != null && `stress ${l.stress_level}/5`].filter(Boolean).join(' · ') || 'No values'}
                      onPress={() => nav.navigate('LifestyleForm', { date: l.date })} accessibilityHint="Opens the entry for editing" />
                  ))}
                </InfoCard>
              )}
            </Section>
            <Section title="Mood">
              {(mood.data ?? []).length === 0 ? <EmptyState title="No mood entries yet" /> : (
                <InfoCard>
                  {(mood.data ?? []).map((m) => <List.Item key={m.id} title={`${m.mood_score} / 5`} description={`${prettyDateTime(m.logged_at)}${m.tags.length ? ` · ${m.tags.join(', ')}` : ''}`} />)}
                </InfoCard>
              )}
            </Section>
          </>
        ) : null}
      </ConsentGate>
    </Screen>
  );
}

type SymptomValues = z.infer<typeof symptomSchema>;
export function SymptomFormScreen({ navigation }: NativeStackScreenProps<RootParamList, 'SymptomForm'>) {
  const create = useCreateSymptom();
  const { control, handleSubmit } = useForm<SymptomValues>({ resolver: zodResolver(symptomSchema) });
  const submit = handleSubmit(async (v) => {
    try { await create.mutateAsync({ symptom_code: v.symptom_code, severity: v.severity, logged_at: nowISO() }); navigation.goBack(); } catch { /* shown below */ }
  });
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">Log a symptom</Text>
      <Controller control={control} name="symptom_code" render={({ field, fieldState }) => (
        <View style={{ gap: 4 }}>
          <Text variant="labelLarge">What are you feeling?</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {SYMPTOM_CODES.map((c) => (
              <Chip key={c} selected={field.value === c} showSelectedCheck accessibilityRole="radio" accessibilityState={{ selected: field.value === c }} onPress={() => field.onChange(c)}>{label(c)}</Chip>
            ))}
          </View>
          <HelperText type="error" visible={!!fieldState.error}>{fieldState.error?.message}</HelperText>
        </View>
      )} />
      <ScoreField control={control} name="severity" label="How strong is it?" lowLabel="mild" highLabel="severe" />
      <FormError error={create.error} />
      <Button mode="contained" onPress={() => void submit()} loading={create.isPending} disabled={create.isPending}>Save</Button>
      <Button onPress={() => navigation.goBack()}>Cancel</Button>
    </Screen>
  );
}

type LifeValues = z.input<typeof lifestyleSchema>;
export function LifestyleFormScreen({ navigation, route }: NativeStackScreenProps<RootParamList, 'LifestyleForm'>) {
  const save = useSaveLifestyle();
  const { control, handleSubmit, reset } = useForm<LifeValues>({
    resolver: zodResolver(lifestyleSchema) as never, defaultValues: { date: route.params?.date ?? today(), nutrition_notes: '' },
  });
  const date = useWatch({ control, name: 'date' }) as string;
  const found = useLifestyle({ date_from: date, date_to: date, limit: 1 });
  const existing = found.data?.find((e) => e.date === date);
  useEffect(() => {
    // one entry per day: editing a day that already has an entry loads it instead of failing with a conflict
    if (existing) reset({ date, sleep_hours: existing.sleep_hours ?? undefined, sleep_quality: (existing.sleep_quality ?? undefined) as never, activity_minutes: existing.activity_minutes ?? undefined, water_ml: existing.water_ml ?? undefined, stress_level: (existing.stress_level ?? undefined) as never, nutrition_notes: '' });
  }, [existing?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = handleSubmit(async (raw) => {
    const v = lifestyleSchema.parse(raw);
    try {
      await save.mutateAsync({ existingId: existing?.id, body: { date: v.date, sleep_hours: v.sleep_hours ?? null, sleep_quality: v.sleep_quality ?? null, activity_minutes: v.activity_minutes ?? null, water_ml: v.water_ml ?? null, stress_level: v.stress_level ?? null, nutrition_notes: v.nutrition_notes || null } });
      navigation.goBack();
    } catch { /* shown below */ }
  });
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">Sleep and lifestyle</Text>
      <DateField control={control} name="date" label="Day" maximumDate={new Date()} />
      {existing ? <Text variant="bodySmall" accessibilityRole="alert">You already have an entry for this day. Saving will update it.</Text> : null}
      <TextField control={control} name="sleep_hours" label="Hours slept" keyboardType="decimal-pad" />
      <ScoreField control={control} name="sleep_quality" label="Sleep quality" lowLabel="poor" highLabel="great" />
      <TextField control={control} name="activity_minutes" label="Active minutes" keyboardType="numeric" />
      <TextField control={control} name="water_ml" label="Water (ml)" keyboardType="numeric" />
      <ScoreField control={control} name="stress_level" label="Stress" lowLabel="calm" highLabel="very stressed" />
      <TextField control={control} name="nutrition_notes" label="Food notes (optional, stored encrypted)" multiline />
      <FormError error={save.error} />
      <Button mode="contained" onPress={() => void submit()} loading={save.isPending} disabled={save.isPending}>{existing ? 'Update' : 'Save'}</Button>
      <Button onPress={() => navigation.goBack()}>Cancel</Button>
    </Screen>
  );
}

type MoodValues = z.infer<typeof moodSchema>;
export function MoodFormScreen({ navigation }: NativeStackScreenProps<RootParamList, 'MoodForm'>) {
  const create = useCreateMood();
  const { control, handleSubmit } = useForm<MoodValues>({ resolver: zodResolver(moodSchema), defaultValues: { tags: [] } });
  const submit = handleSubmit(async (v) => {
    try { await create.mutateAsync({ mood_score: v.mood_score, tags: v.tags, logged_at: nowISO() }); navigation.goBack(); } catch { /* shown below */ }
  });
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">How is your mood?</Text>
      <ScoreField control={control} name="mood_score" label="Mood" lowLabel="low" highLabel="great" />
      <ChipsField control={control} name="tags" label="What describes it? (optional)" options={MOOD_TAGS} />
      <FormError error={create.error} />
      <Button mode="contained" onPress={() => void submit()} loading={create.isPending} disabled={create.isPending}>Save</Button>
      <Button onPress={() => navigation.goBack()}>Cancel</Button>
    </Screen>
  );
}
