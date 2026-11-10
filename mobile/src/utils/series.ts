import { addDays, format, parseISO } from 'date-fns';

import type { LifestyleOut, MoodOut } from '@/types/api';

import { toISODate } from './dates';

/** Last `n` calendar days ending at `end` (inclusive), oldest first. */
export const lastDays = (n: number, end: Date = new Date()): string[] =>
  Array.from({ length: n }, (_, i) => toISODate(addDays(end, i - (n - 1))));

export const weekdayLabel = (iso: string): string => format(parseISO(iso), 'EEEEE');

export function sleepSeries(entries: Pick<LifestyleOut, 'date' | 'sleep_hours'>[], days: string[]) {
  const byDate = new Map(entries.map((e) => [e.date, e.sleep_hours]));
  return days.map((d) => ({ label: weekdayLabel(d), value: byDate.get(d) ?? null }));
}

/** Mean mood score per local day (several entries a day are averaged); days without entries are null. */
export function moodSeries(entries: Pick<MoodOut, 'logged_at' | 'mood_score'>[], days: string[]) {
  const sums = new Map<string, number[]>();
  for (const e of entries) {
    const k = toISODate(new Date(e.logged_at));
    sums.set(k, [...(sums.get(k) ?? []), e.mood_score]);
  }
  return days.map((d) => {
    const v = sums.get(d);
    return { label: weekdayLabel(d), value: v ? Math.round((v.reduce((a, b) => a + b, 0) / v.length) * 10) / 10 : null };
  });
}
