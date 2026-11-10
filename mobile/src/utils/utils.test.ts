import { buildMonth, periodDays } from './cycleCalendar';
import { cycleDay, daysAgo, isISODate, parseDate, toISODate } from './dates';
import { lastDays, moodSeries, sleepSeries } from './series';

describe('dates', () => {
  it('validates ISO calendar dates strictly', () => {
    expect(isISODate('2026-02-28')).toBe(true);
    for (const bad of ['2026-02-30', '2026-13-01', '26-01-01', '2026/01/01', '', 'garbage']) expect(isISODate(bad)).toBe(false);
  });
  it('round-trips dates in local time', () => expect(toISODate(parseDate('2026-03-01'))).toBe('2026-03-01'));
  it('computes days ago', () => expect(daysAgo(3, new Date(2026, 2, 5))).toBe('2026-03-02'));
  it('computes cycle day (1-based) and never negative', () => {
    expect(cycleDay('2026-03-01', '2026-03-01')).toBe(1);
    expect(cycleDay('2026-03-01', '2026-03-29')).toBe(29);
    expect(cycleDay('2026-03-10', '2026-03-01')).toBeNull();
    expect(cycleDay(undefined)).toBeNull();
  });
});

describe('cycle calendar', () => {
  it('marks every day of a period inclusively, open periods mark only the start', () => {
    const d = periodDays([{ start_date: '2026-03-02', end_date: '2026-03-05' }, { start_date: '2026-03-20', end_date: null }]);
    expect([...d].sort()).toEqual(['2026-03-02', '2026-03-03', '2026-03-04', '2026-03-05', '2026-03-20']);
  });
  it('ignores malformed ranges', () => expect(periodDays([{ start_date: '2026-03-05', end_date: '2026-03-01' }]).size).toBe(0));
  it('builds Monday-first whole weeks and flags in-month, period and today', () => {
    const weeks = buildMonth(new Date(2026, 2, 15), [{ start_date: '2026-03-30', end_date: '2026-04-02' }], new Date(2026, 2, 15));
    expect(weeks.every((w) => w.length === 7)).toBe(true);
    expect(weeks[0]![0]!.date).toBe('2026-02-23'); // 1 Mar 2026 is a Sunday -> grid starts Monday 23 Feb
    expect(weeks[0]![0]!.inMonth).toBe(false);
    const flat = weeks.flat();
    expect(flat.filter((c) => c.isToday).map((c) => c.date)).toEqual(['2026-03-15']);
    expect(flat.filter((c) => c.isPeriod).map((c) => c.date)).toEqual(['2026-03-30', '2026-03-31', '2026-04-01', '2026-04-02']);
    expect(flat.find((c) => c.date === '2026-04-01')!.inMonth).toBe(false); // period days spill into next month's padding
  });
});

describe('series', () => {
  const end = new Date(2026, 2, 10);
  it('lists the last n days oldest first', () => {
    const d = lastDays(7, end);
    expect(d).toHaveLength(7);
    expect([d[0], d[6]]).toEqual(['2026-03-04', '2026-03-10']);
  });
  it('leaves missing sleep as null, never zero', () => {
    const s = sleepSeries([{ date: '2026-03-10', sleep_hours: 7.5 }], lastDays(3, end));
    expect(s.map((x) => x.value)).toEqual([null, null, 7.5]);
  });
  it('averages several mood entries on one local day', () => {
    const day = new Date(2026, 2, 10, 9).toISOString();
    const day2 = new Date(2026, 2, 10, 20).toISOString();
    const s = moodSeries([{ logged_at: day, mood_score: 2 }, { logged_at: day2, mood_score: 5 }], lastDays(2, end));
    expect(s.map((x) => x.value)).toEqual([null, 3.5]);
  });
});
