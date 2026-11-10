import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import React from 'react';
import { View } from 'react-native';
import { Button, List, Text } from 'react-native-paper';

import { toApiError } from '@/api/errors';
import { useCycles, useCycleStats, useLifestyle, useLifestyleSummary, useMood, useSymptoms } from '@/api/hooks';
import { useAuth } from '@/auth/AuthContext';
import { BarChart } from '@/components/BarChart';
import { ConsentGate } from '@/components/ConsentGate';
import { ErrorState, InfoCard, Loading, Screen, Section } from '@/components/ui';
import { DISCLAIMER } from '@/config';
import type { RootParamList, TabParamList } from '@/navigation/types';
import { cycleDay, prettyDate, prettyDateTime } from '@/utils/dates';
import { lastDays, moodSeries, sleepSeries } from '@/utils/series';
import type { CompositeScreenProps } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = CompositeScreenProps<BottomTabScreenProps<TabParamList, 'Home'>, NativeStackScreenProps<RootParamList>>;

export function HomeScreen({ navigation }: Props) {
  const { user } = useAuth();
  const days = lastDays(7);
  const range = { date_from: days[0], date_to: days[6], limit: 14 };
  const cycles = useCycles({ limit: 1 });
  const stats = useCycleStats();
  const summary = useLifestyleSummary(7);
  const lifestyle = useLifestyle(range);
  const mood = useMood({ date_from: `${days[0]}T00:00:00Z`, limit: 50 });
  const symptoms = useSymptoms({ limit: 5 });

  const all = [cycles, stats, summary, lifestyle, mood, symptoms];
  const firstError = all.find((q) => q.error)?.error;
  const consentBlocked = !!firstError && toApiError(firstError).isConsentRequired;
  const refreshing = all.some((q) => q.isFetching && !q.isLoading);
  const refetchAll = () => all.forEach((q) => void q.refetch());
  const last = cycles.data?.[0];
  const day = cycleDay(last?.start_date);

  return (
    <Screen onRefresh={refetchAll} refreshing={refreshing}>
      <Text variant="headlineSmall" accessibilityRole="header">{`Hello, ${user?.display_name ?? ''}`}</Text>
      <ConsentGate error={firstError}>
        {all.some((q) => q.isLoading) ? <Loading /> : null}
        {firstError && !consentBlocked ? <ErrorState error={firstError} onRetry={refetchAll} /> : null}
        {!firstError && !all.some((q) => q.isLoading) ? (
          <>
            <Section title="Your cycle">
              <InfoCard tone="soft">
                {last ? (
                  <>
                    <Text variant="displaySmall" accessibilityLabel={`Cycle day ${day ?? 'unknown'}`}>{day ? `Day ${day}` : '-'}</Text>
                    <Text>{`Last period started ${prettyDate(last.start_date)}`}</Text>
                    <Text>
                      {stats.data?.mean_length != null
                        ? `Average cycle length ${stats.data.mean_length} days (from ${stats.data.n_cycles} recorded ${stats.data.n_cycles === 1 ? 'cycle' : 'cycles'})`
                        : 'Log at least two periods to see your average cycle length.'}
                    </Text>
                  </>
                ) : <Text>No periods logged yet. Start with your most recent period.</Text>}
                <Button mode="contained" onPress={() => navigation.navigate('CycleForm')}>Log period</Button>
              </InfoCard>
            </Section>

            <Section title="Last 7 days">
              <InfoCard>
                <Text>
                  {summary.data && summary.data.n_entries > 0
                    ? `Sleep ${summary.data.avg_sleep_hours ?? '-'} h on average · activity ${summary.data.avg_activity_minutes ?? '-'} min · stress ${summary.data.avg_stress ?? '-'}/5 (${summary.data.n_entries} ${summary.data.n_entries === 1 ? 'day' : 'days'} logged)`
                    : 'No sleep or lifestyle entries this week.'}
                </Text>
                <Text variant="labelLarge">Sleep (hours)</Text>
                <BarChart title="Sleep hours, last 7 days" data={sleepSeries(lifestyle.data ?? [], days)} max={12} unit="hours" />
                <Text variant="labelLarge">Mood (1 low - 5 high)</Text>
                <BarChart title="Average mood, last 7 days" data={moodSeries(mood.data ?? [], days)} max={5} unit="out of 5" />
              </InfoCard>
            </Section>

            <Section title="Recent symptoms">
              <InfoCard>
                {symptoms.data && symptoms.data.length > 0 ? symptoms.data.map((s) => (
                  <List.Item key={s.id} title={s.symptom_code.replace(/_/g, ' ')} description={`${prettyDateTime(s.logged_at)} · severity ${s.severity}/5`} />
                )) : <Text>No symptoms logged yet.</Text>}
              </InfoCard>
            </Section>

            <Section title="Log something">
              <View style={{ gap: 8 }}>
                <Button mode="outlined" icon="emoticon-sad-outline" onPress={() => navigation.navigate('SymptomForm')}>Symptom</Button>
                <Button mode="outlined" icon="sleep" onPress={() => navigation.navigate('LifestyleForm')}>Sleep and lifestyle</Button>
                <Button mode="outlined" icon="emoticon-happy-outline" onPress={() => navigation.navigate('MoodForm')}>Mood</Button>
              </View>
            </Section>
          </>
        ) : null}
      </ConsentGate>
      <Text variant="bodySmall">{DISCLAIMER}</Text>
    </Screen>
  );
}
