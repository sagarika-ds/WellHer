import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import React from 'react';
import { Text } from 'react-native';

import { renderWithProviders } from '@/__tests__/testUtils';
import { ApiError } from '@/api/errors';

import { BarChart } from './BarChart';
import { ConsentGate } from './ConsentGate';
import { CycleCalendar } from './CycleCalendar';

jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
import { endpoints, type Endpoints } from '@/api/endpoints';
const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;

describe('ConsentGate', () => {
  it('renders children when there is no error or a different error', async () => {
    await renderWithProviders(<ConsentGate error={null}><Text>secret content</Text></ConsentGate>);
    expect(screen.getByText('secret content')).toBeTruthy();
    await renderWithProviders(<ConsentGate error={new ApiError(500, 'internal_error', 'x')}><Text>other content</Text></ConsentGate>);
    expect(screen.getByText('other content')).toBeTruthy();
  });
  it('replaces content with a consent prompt when the SERVER says consent is required, and grants on tap', async () => {
    ep.setConsent.mockResolvedValue({});
    await renderWithProviders(<ConsentGate error={new ApiError(403, 'consent_required', 'Consent required')}><Text>secret content</Text></ConsentGate>);
    expect(screen.queryByText('secret content')).toBeNull();
    await fireEvent.press(screen.getByText('Turn on health tracking'));
    await waitFor(() => expect(ep.setConsent).toHaveBeenCalledWith('health_tracking', true));
  });
});

describe('CycleCalendar', () => {
  const cycles = [{ start_date: '2026-03-02', end_date: '2026-03-04' }];
  it('labels period days for screen readers and navigates months', async () => {
    const onMonthChange = jest.fn();
    await renderWithProviders(<CycleCalendar month={new Date(2026, 2, 10)} onMonthChange={onMonthChange} cycles={cycles} />);
    expect(screen.getByText('March 2026')).toBeTruthy();
    expect(screen.getByLabelText('3 March, period day')).toBeTruthy();
    expect(screen.getByLabelText('10 March')).toBeTruthy();
    expect(screen.queryByLabelText('10 March, period day')).toBeNull();
    await fireEvent.press(screen.getByLabelText('Next month'));
    expect(onMonthChange.mock.calls[0]![0].getMonth()).toBe(3);
    await fireEvent.press(screen.getByLabelText('Previous month'));
    expect(onMonthChange.mock.calls[1]![0].getMonth()).toBe(1);
  });
  it('reports the tapped day', async () => {
    const onSelectDay = jest.fn();
    await renderWithProviders(<CycleCalendar month={new Date(2026, 2, 10)} onMonthChange={jest.fn()} cycles={[]} onSelectDay={onSelectDay} />);
    await fireEvent.press(screen.getByLabelText('15 March'));
    expect(onSelectDay).toHaveBeenCalledWith('2026-03-15');
  });
});

describe('BarChart', () => {
  it('describes values for screen readers and distinguishes "no entry" from zero', async () => {
    await renderWithProviders(<BarChart title="Sleep" unit="hours" max={12} data={[{ label: 'M', value: 7.5 }, { label: 'T', value: null }, { label: 'W', value: 0 }]} />);
    expect(screen.getByLabelText('Sleep. M 7.5 hours, T no entry, W 0 hours')).toBeTruthy();
  });
});
