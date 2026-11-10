import { addDays, format, parseISO, startOfDay, differenceInCalendarDays } from 'date-fns';

/** Calendar dates are plain `YYYY-MM-DD` strings in the LOCAL timezone (the API's date columns have no zone). */
export const toISODate = (d: Date): string => format(d, 'yyyy-MM-dd');
export const parseDate = (s: string): Date => parseISO(s);
export const today = (): string => toISODate(new Date());
export const isISODate = (s: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(parseISO(s).getTime()) && toISODate(parseISO(s)) === s;
export const daysAgo = (n: number, from: Date = new Date()): string => toISODate(addDays(startOfDay(from), -n));
export const daysBetween = (a: string, b: string): number => differenceInCalendarDays(parseISO(b), parseISO(a));
export const prettyDate = (s: string): string => format(parseISO(s), 'd MMM yyyy');
export const prettyDateTime = (iso: string): string => format(new Date(iso), 'd MMM, HH:mm');

/** Timestamps sent to the API must carry an offset; `toISOString()` gives UTC with `Z`. */
export const nowISO = (): string => new Date().toISOString();

/** 1-based cycle day for `date` given the most recent period start (no prediction involved). */
export function cycleDay(lastStart: string | undefined, on: string = today()): number | null {
  if (!lastStart) return null;
  const n = daysBetween(lastStart, on) + 1;
  return n >= 1 ? n : null;
}
