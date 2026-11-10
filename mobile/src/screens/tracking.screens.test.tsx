import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import React from 'react';
import { Alert } from 'react-native';

import { renderWithProviders, sp } from '@/__tests__/testUtils';
import { ApiError } from '@/api/errors';
import { daysAgo, today } from '@/utils/dates';

import { CycleFormScreen, CycleScreen } from './cycle/CycleScreens';
import { HomeScreen } from './dashboard/HomeScreen';
import { LifestyleFormScreen, LogScreen, MoodFormScreen, SymptomFormScreen } from './log/LogScreens';

const mockNav = { navigate: jest.fn(), goBack: jest.fn() };
jest.mock('@/navigation/hooks', () => ({ useRootNav: () => mockNav }));
jest.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { id: 'u', email: 'a@b.co', display_name: 'Asha', role: 'user' } }) }));
jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
import { endpoints, type Endpoints } from '@/api/endpoints';
const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;
const consentError = () => new ApiError(403, 'consent_required', 'Consent for health_tracking is required.');

function stubHome(over: Record<string, unknown> = {}) {
  ep.listCycles.mockResolvedValue([{ id: 'c1', start_date: daysAgo(9), end_date: null, cycle_length_days: null, flow_intensity: 2, notes: null }]);
  ep.cycleStats.mockResolvedValue({ n_cycles: 3, mean_length: 28.5, std_length: 1.2, min: 27, max: 30 });
  ep.lifestyleSummary.mockResolvedValue({ period_days: 7, n_entries: 4, avg_sleep_hours: 6.8, avg_activity_minutes: 35, avg_stress: 2.5 });
  ep.listLifestyle.mockResolvedValue([{ id: 'l1', date: today(), sleep_hours: 7, sleep_quality: 4, activity_minutes: 30, water_ml: 1500, stress_level: 2 }]);
  ep.listMood.mockResolvedValue([{ id: 'm1', logged_at: new Date().toISOString(), mood_score: 4, tags: ['calm'] }]);
  ep.listSymptoms.mockResolvedValue([{ id: 's1', logged_at: new Date().toISOString(), symptom_code: 'back_pain', severity: 3, cycle_id: null }]);
  Object.entries(over).forEach(([k, v]) => ep[k as keyof Endpoints].mockImplementation(v as never));
}
const EP_KEYS = ['listCycles', 'createCycle', 'updateCycle', 'deleteCycle', 'cycleStats', 'listSymptoms', 'createSymptom', 'listLifestyle',
  'createLifestyle', 'updateLifestyle', 'lifestyleSummary', 'listMood', 'createMood', 'setConsent'] as (keyof Endpoints)[];
beforeEach(() => { EP_KEYS.forEach((k) => ep[k].mockReset()); mockNav.navigate.mockReset(); mockNav.goBack.mockReset(); jest.restoreAllMocks(); });

describe('HomeScreen', () => {
  it('shows real cycle facts computed from records (no predictions)', async () => {
    stubHome();
    await renderWithProviders(<HomeScreen {...sp({ navigation: mockNav, route: {} })} />);
    expect(await screen.findByText('Hello, Asha')).toBeTruthy();
    expect(await screen.findByLabelText('Cycle day 10')).toBeTruthy();
    expect(screen.getByText('Average cycle length 28.5 days (from 3 recorded cycles)')).toBeTruthy();
    expect(screen.getByText(/Sleep 6.8 h on average/)).toBeTruthy();
    expect(screen.getByText('back pain')).toBeTruthy();
    expect(screen.getByLabelText(/^Sleep hours, last 7 days\./)).toBeTruthy();
  });
  it('handles a brand-new account with honest empty states', async () => {
    stubHome({ listCycles: async () => [], cycleStats: async () => ({ n_cycles: 0, mean_length: null, std_length: null, min: null, max: null }),
      lifestyleSummary: async () => ({ period_days: 7, n_entries: 0, avg_sleep_hours: null, avg_activity_minutes: null, avg_stress: null }), listLifestyle: async () => [], listMood: async () => [], listSymptoms: async () => [] });
    await renderWithProviders(<HomeScreen {...sp({ navigation: mockNav, route: {} })} />);
    expect(await screen.findByText('No periods logged yet. Start with your most recent period.')).toBeTruthy();
    expect(screen.getByText('No symptoms logged yet.')).toBeTruthy();
    expect(screen.getByText('No sleep or lifestyle entries this week.')).toBeTruthy();
  });
  it('replaces health content with the consent prompt when the server withholds it', async () => {
    stubHome();
    (['listCycles', 'cycleStats', 'lifestyleSummary', 'listLifestyle', 'listMood', 'listSymptoms'] as (keyof Endpoints)[]).forEach((k) => ep[k].mockRejectedValue(consentError()));
    await renderWithProviders(<HomeScreen {...sp({ navigation: mockNav, route: {} })} />);
    expect(await screen.findByText('Health tracking is turned off')).toBeTruthy();
    expect(screen.queryByText('Your cycle')).toBeNull();
  });
  it('shows an offline state with retry instead of a blank screen', async () => {
    stubHome();
    ep.listCycles.mockRejectedValue(new ApiError(0, 'network_error', "Can't reach the server. Check your connection and try again."));
    await renderWithProviders(<HomeScreen {...sp({ navigation: mockNav, route: {} })} />);
    expect(await screen.findByText("You're offline")).toBeTruthy();
    await fireEvent.press(screen.getByText('Try again'));
    await waitFor(() => expect(ep.listCycles.mock.calls.length).toBeGreaterThan(1));
  });
  it('quick actions open the right forms', async () => {
    stubHome();
    await renderWithProviders(<HomeScreen {...sp({ navigation: mockNav, route: {} })} />);
    await fireEvent.press(await screen.findByText('Symptom'));
    await fireEvent.press(screen.getByText('Mood'));
    await fireEvent.press(screen.getByText('Log period'));
    expect(mockNav.navigate.mock.calls.map((c) => c[0])).toEqual(['SymptomForm', 'MoodForm', 'CycleForm']);
  });
});

describe('Cycle screens', () => {
  it('lists history with computed cycle lengths and confirms before deleting', async () => {
    ep.listCycles.mockResolvedValue([
      { id: 'c2', start_date: '2026-03-01', end_date: '2026-03-05', cycle_length_days: null, flow_intensity: 3, notes: null },
      { id: 'c1', start_date: '2026-02-01', end_date: '2026-02-04', cycle_length_days: 28, flow_intensity: 2, notes: null }]);
    ep.deleteCycle.mockResolvedValue(undefined);
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    await renderWithProviders(<CycleScreen />);
    expect(await screen.findByText('28-day cycle')).toBeTruthy();
    expect(screen.getByText('Latest cycle')).toBeTruthy();
    await fireEvent.press(screen.getByLabelText('Delete period starting 1 Mar 2026'));
    expect(ep.deleteCycle).not.toHaveBeenCalled(); // nothing is deleted without confirmation
    const destructive = (alert.mock.calls[0]![2] as { text: string; onPress?: () => void }[]).find((b) => b.text === 'Delete')!;
    destructive.onPress!();
    await waitFor(() => expect(ep.deleteCycle).toHaveBeenCalledWith('c2'));
  });
  it('creates a period with defaults and returns to the previous screen', async () => {
    ep.listCycles.mockResolvedValue([]); ep.createCycle.mockResolvedValue({});
    await renderWithProviders(<CycleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.createCycle).toHaveBeenCalledWith({ start_date: today(), end_date: null, flow_intensity: null, notes: null }));
    expect(mockNav.goBack).toHaveBeenCalled();
  });
  it('shows the server conflict message and stays on the form', async () => {
    ep.listCycles.mockResolvedValue([]);
    ep.createCycle.mockRejectedValue(new ApiError(409, 'conflict', 'This period overlaps an existing record starting 2026-01-10.'));
    await renderWithProviders(<CycleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    await fireEvent.press(screen.getByText('Save'));
    expect(await screen.findByText(/overlaps an existing record/)).toBeTruthy();
    expect(mockNav.goBack).not.toHaveBeenCalled();
  });
  it('editing prefills the record and updates (not creates) it', async () => {
    ep.listCycles.mockResolvedValue([{ id: 'c9', start_date: '2026-03-01', end_date: '2026-03-05', cycle_length_days: null, flow_intensity: 2, notes: 'note' }]);
    ep.updateCycle.mockResolvedValue({});
    await renderWithProviders(<CycleFormScreen {...sp({ navigation: mockNav, route: { params: { cycleId: 'c9' } } })} />);
    expect(await screen.findByText('Edit period')).toBeTruthy();
    expect(await screen.findByLabelText('First day: 1 Mar 2026. Change')).toBeTruthy();
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.updateCycle).toHaveBeenCalledWith('c9', { start_date: '2026-03-01', end_date: '2026-03-05', flow_intensity: 2, notes: 'note' }));
    expect(ep.createCycle).not.toHaveBeenCalled();
  });
});

describe('Log screens', () => {
  it('symptom form requires a symptom, then saves it with severity and a timezone-aware timestamp', async () => {
    ep.createSymptom.mockResolvedValue({});
    await renderWithProviders(<SymptomFormScreen {...sp({ navigation: mockNav, route: {} })} />);
    await fireEvent.press(screen.getByText('Save'));
    expect(await screen.findByText('Choose a symptom')).toBeTruthy();
    expect(ep.createSymptom).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByText('headache'));
    await fireEvent.press(screen.getByLabelText('How strong is it? 3 of 5'));
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.createSymptom).toHaveBeenCalled());
    const body = ep.createSymptom.mock.calls[0]![0];
    expect(body).toMatchObject({ symptom_code: 'headache', severity: 3 });
    expect(body.logged_at).toMatch(/Z$/);
  });
  it('mood form saves score and tags', async () => {
    ep.createMood.mockResolvedValue({});
    await renderWithProviders(<MoodFormScreen {...sp({ navigation: mockNav, route: {} })} />);
    await fireEvent.press(screen.getByLabelText('Mood 4 of 5'));
    await fireEvent.press(screen.getByText('calm'));
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.createMood).toHaveBeenCalled());
    expect(ep.createMood.mock.calls[0]![0]).toMatchObject({ mood_score: 4, tags: ['calm'] });
  });
  it('lifestyle form creates a new day entry with unset fields sent as null (never 0)', async () => {
    ep.listLifestyle.mockResolvedValue([]); ep.createLifestyle.mockResolvedValue({});
    await renderWithProviders(<LifestyleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    await fireEvent.changeText(screen.getByLabelText('Hours slept'), '7.5');
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.createLifestyle).toHaveBeenCalledWith({ date: today(), sleep_hours: 7.5, sleep_quality: null, activity_minutes: null, water_ml: null, stress_level: null, nutrition_notes: null }));
  });
  it('an empty sleep field is saved as null, never as 0 hours (0 would be a false record)', async () => {
    ep.listLifestyle.mockResolvedValue([]); ep.createLifestyle.mockResolvedValue({});
    await renderWithProviders(<LifestyleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    await fireEvent.changeText(screen.getByLabelText('Active minutes'), '20');
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.createLifestyle).toHaveBeenCalled());
    expect(ep.createLifestyle.mock.calls[0]![0]).toMatchObject({ sleep_hours: null, activity_minutes: 20, water_ml: null });
  });
  it('lifestyle form rejects impossible values locally', async () => {
    ep.listLifestyle.mockResolvedValue([]);
    await renderWithProviders(<LifestyleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    await fireEvent.changeText(screen.getByLabelText('Hours slept'), '25');
    await fireEvent.press(screen.getByText('Save'));
    expect(await screen.findByText('Sleep must be at most 24')).toBeTruthy();
    expect(ep.createLifestyle).not.toHaveBeenCalled();
  });
  it('lifestyle form updates the existing entry for that day instead of hitting a duplicate-date conflict', async () => {
    ep.listLifestyle.mockResolvedValue([{ id: 'L1', date: today(), sleep_hours: 6.5, sleep_quality: 3, activity_minutes: 20, water_ml: null, stress_level: 2 }]);
    ep.updateLifestyle.mockResolvedValue({});
    await renderWithProviders(<LifestyleFormScreen {...sp({ navigation: mockNav, route: { params: undefined } })} />);
    expect(await screen.findByText('You already have an entry for this day. Saving will update it.')).toBeTruthy();
    await fireEvent.press(screen.getByText('Update'));
    await waitFor(() => expect(ep.updateLifestyle).toHaveBeenCalledWith('L1', expect.objectContaining({ date: today(), sleep_hours: 6.5, activity_minutes: 20 })));
    expect(ep.createLifestyle).not.toHaveBeenCalled();
  });
  it('log hub lists recent entries and offers the three forms', async () => {
    stubHome();
    await renderWithProviders(<LogScreen />);
    expect(await screen.findByText('back pain')).toBeTruthy();
    await fireEvent.press(screen.getByText('Log a symptom'));
    await fireEvent.press(screen.getByText('Log sleep and lifestyle'));
    await fireEvent.press(screen.getByText('Log mood'));
    expect(mockNav.navigate.mock.calls.map((c) => c[0])).toEqual(['SymptomForm', 'LifestyleForm', 'MoodForm']);
  });
});
