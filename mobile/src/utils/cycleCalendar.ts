import { addMonths, eachDayOfInterval, endOfMonth, endOfWeek, startOfMonth, startOfWeek } from 'date-fns';

import type { CycleOut } from '@/types/api';

import { toISODate } from './dates';

export type CalendarDay = { date: string; day: number; inMonth: boolean; isPeriod: boolean; isToday: boolean };

/** Days (ISO) covered by logged periods. An open period (no end date) marks its start day only. */
export function periodDays(cycles: Pick<CycleOut, 'start_date' | 'end_date'>[]): Set<string> {
  const out = new Set<string>();
  for (const c of cycles) {
    const start = new Date(`${c.start_date}T00:00:00`);
    const end = c.end_date ? new Date(`${c.end_date}T00:00:00`) : start;
    if (end < start) continue;
    for (const d of eachDayOfInterval({ start, end })) out.add(toISODate(d));
  }
  return out;
}

/** Monday-first month grid (always whole weeks). */
export function buildMonth(month: Date, cycles: Pick<CycleOut, 'start_date' | 'end_date'>[], now: Date = new Date()): CalendarDay[][] {
  const marked = periodDays(cycles);
  const todayISO = toISODate(now);
  const days = eachDayOfInterval({
    start: startOfWeek(startOfMonth(month), { weekStartsOn: 1 }),
    end: endOfWeek(endOfMonth(month), { weekStartsOn: 1 }),
  });
  const cells = days.map((d) => ({
    date: toISODate(d), day: d.getDate(), inMonth: d.getMonth() === month.getMonth(),
    isPeriod: marked.has(toISODate(d)), isToday: toISODate(d) === todayISO,
  }));
  const weeks: CalendarDay[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

export const shiftMonth = (month: Date, by: number): Date => addMonths(month, by);
