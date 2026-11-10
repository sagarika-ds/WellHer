import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Alert, View } from 'react-native';
import { Button, List, Text } from 'react-native-paper';
import type { z } from 'zod';

import { toApiError } from '@/api/errors';
import { useCreateCycle, useCycles, useDeleteCycle, useUpdateCycle } from '@/api/hooks';
import { CycleCalendar } from '@/components/CycleCalendar';
import { ConsentGate } from '@/components/ConsentGate';
import { DateField, ScoreField, TextField } from '@/components/forms';
import { EmptyState, ErrorState, FormError, InfoCard, Loading, Screen, Section } from '@/components/ui';
import { useRootNav } from '@/navigation/hooks';
import type { RootParamList } from '@/navigation/types';
import { prettyDate, today } from '@/utils/dates';
import { cycleSchema } from '@/utils/validation';

export function CycleScreen() {
  const navigation = useRootNav();
  const [month, setMonth] = useState(new Date());
  const cycles = useCycles({ limit: 100 });
  const del = useDeleteCycle();

  const confirmDelete = (id: string, start: string) =>
    Alert.alert('Delete this period?', `The period starting ${prettyDate(start)} will be removed.`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => del.mutate(id) },
    ]);

  return (
    <Screen onRefresh={() => void cycles.refetch()} refreshing={cycles.isRefetching}>
      <ConsentGate error={cycles.error}>
        {cycles.isLoading ? <Loading /> : null}
        {cycles.error && !toApiError(cycles.error).isConsentRequired ? <ErrorState error={cycles.error} onRetry={() => void cycles.refetch()} /> : null}
        {cycles.data ? (
          <>
            <InfoCard><CycleCalendar month={month} onMonthChange={setMonth} cycles={cycles.data} /></InfoCard>
            <Button mode="contained" icon="plus" onPress={() => navigation.navigate('CycleForm')}>Log period</Button>
            <FormError error={del.error} />
            <Section title="History">
              {cycles.data.length === 0 ? <EmptyState title="No periods logged yet" hint="Log your most recent period to start your calendar." /> : (
                <InfoCard>
                  {cycles.data.map((c) => (
                    <List.Item key={c.id}
                      title={`${prettyDate(c.start_date)}${c.end_date ? ` - ${prettyDate(c.end_date)}` : ' (ongoing)'}`}
                      description={c.cycle_length_days ? `${c.cycle_length_days}-day cycle` : 'Latest cycle'}
                      onPress={() => navigation.navigate('CycleForm', { cycleId: c.id })}
                      accessibilityHint="Opens the entry for editing"
                      right={() => <Button onPress={() => confirmDelete(c.id, c.start_date)} accessibilityLabel={`Delete period starting ${prettyDate(c.start_date)}`}>Delete</Button>} />
                  ))}
                </InfoCard>
              )}
            </Section>
          </>
        ) : null}
      </ConsentGate>
    </Screen>
  );
}

type FormValues = z.infer<typeof cycleSchema>;

export function CycleFormScreen({ navigation, route }: NativeStackScreenProps<RootParamList, 'CycleForm'>) {
  const cycleId = route.params?.cycleId;
  const cycles = useCycles({ limit: 100 });
  const create = useCreateCycle();
  const update = useUpdateCycle();
  const existing = cycleId ? cycles.data?.find((c) => c.id === cycleId) : undefined;
  const { control, handleSubmit, reset, formState: { isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(cycleSchema), defaultValues: { start_date: today(), end_date: '', flow_intensity: undefined, notes: '' },
  });
  useEffect(() => {
    if (existing) reset({ start_date: existing.start_date, end_date: existing.end_date ?? '', flow_intensity: (existing.flow_intensity ?? undefined) as FormValues['flow_intensity'], notes: existing.notes ?? '' });
  }, [existing, reset]);

  const saving = create.isPending || update.isPending;
  const error = create.error ?? update.error;
  const submit = handleSubmit(async (v) => {
    const body = { start_date: v.start_date, end_date: v.end_date || null, flow_intensity: v.flow_intensity ?? null, notes: v.notes || null };
    try {
      if (cycleId) await update.mutateAsync({ id: cycleId, body }); else await create.mutateAsync(body);
      navigation.goBack();
    } catch { /* surfaced via FormError below */ }
  });

  if (cycleId && cycles.isLoading) return <Loading />;
  return (
    <Screen>
      <Text variant="titleLarge" accessibilityRole="header">{cycleId ? 'Edit period' : 'Log a period'}</Text>
      <DateField control={control} name="start_date" label="First day" maximumDate={new Date()} />
      <DateField control={control} name="end_date" label="Last day" optional maximumDate={new Date()} />
      <ScoreField control={control} name="flow_intensity" label="Flow" lowLabel="light" highLabel="heavy" />
      <TextField control={control} name="notes" label="Notes (optional, stored encrypted)" multiline />
      <FormError error={error} />
      <View style={{ gap: 8 }}>
        <Button mode="contained" onPress={() => void submit()} loading={saving || isSubmitting} disabled={saving || isSubmitting}>Save</Button>
        <Button onPress={() => navigation.goBack()}>Cancel</Button>
      </View>
    </Screen>
  );
}
