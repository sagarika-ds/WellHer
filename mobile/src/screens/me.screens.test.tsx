import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import React from 'react';
import { Alert, Share } from 'react-native';

import { renderWithProviders, sp } from '@/__tests__/testUtils';
import { ApiError } from '@/api/errors';

import { AccessHistoryScreen, AISettingsScreen, ConsentsScreen, DeleteAccountScreen, MeScreen, ProfileEditScreen } from './me/MeScreens';

const mockNav = { navigate: jest.fn(), goBack: jest.fn() };
const mockAuth = { user: { id: 'u', email: 'asha@example.com', display_name: 'Asha', role: 'user' }, logout: jest.fn() };
jest.mock('@/navigation/hooks', () => ({ useRootNav: () => mockNav }));
jest.mock('@/auth/AuthContext', () => ({ useAuth: () => mockAuth }));
jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
import { endpoints, type Endpoints } from '@/api/endpoints';
const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;

const consents = (granted: string[]) => ['health_tracking', 'ml_processing', 'llm_external', 'analytics'].map((purpose) => ({
  purpose, granted: granted.includes(purpose), version: 'v1', granted_at: granted.includes(purpose) ? '2026-03-01T10:00:00Z' : null, revoked_at: null }));
const AI = { personalization_enabled: true, external_llm_allowed: false, context_allowlist: [] as string[], chat_retention_days: 30 };
const EP_KEYS = ['getConsents', 'setConsent', 'getAISettings', 'putAISettings', 'accessHistory', 'exportData', 'deleteAccount', 'getProfile', 'putProfile'] as (keyof Endpoints)[];
beforeEach(() => { EP_KEYS.forEach((k) => ep[k].mockReset()); mockNav.navigate.mockReset(); mockNav.goBack.mockReset(); mockAuth.logout.mockReset(); jest.restoreAllMocks(); });

describe('ConsentsScreen', () => {
  it('reflects server state and changes exactly the toggled purpose', async () => {
    ep.getConsents.mockResolvedValue(consents(['health_tracking']));
    ep.setConsent.mockResolvedValue({});
    await renderWithProviders(<ConsentsScreen />);
    await screen.findByText('Health tracking');
    expect(screen.getByTestId('consent-health_tracking').props.value).toBe(true);
    expect(screen.getByTestId('consent-llm_external').props.value).toBe(false);
    await fireEvent(screen.getByTestId('consent-llm_external'), 'valueChange', true);
    await waitFor(() => expect(ep.setConsent).toHaveBeenCalledWith('llm_external', true));
    await fireEvent(screen.getByTestId('consent-health_tracking'), 'valueChange', false);
    await waitFor(() => expect(ep.setConsent).toHaveBeenCalledWith('health_tracking', false));
  });
  it('is honest that insight features are not available yet', async () => {
    ep.getConsents.mockResolvedValue(consents([]));
    await renderWithProviders(<ConsentsScreen />);
    expect(await screen.findByText(/Insight features arrive in a later version/)).toBeTruthy();
  });
});

describe('AISettingsScreen', () => {
  it('cannot enable external AI until that consent has been granted', async () => {
    ep.getAISettings.mockResolvedValue(AI); ep.getConsents.mockResolvedValue(consents(['health_tracking']));
    await renderWithProviders(<AISettingsScreen {...sp({ navigation: mockNav, route: {} })} />);
    await screen.findByText('Allow external AI providers');
    expect(screen.getByTestId('ai-external').props.disabled).toBe(true);
    expect(screen.getByText(/Requires the "External AI providers" consent first/)).toBeTruthy();
  });
  it('saves the allowlist and switches the user chose', async () => {
    ep.getAISettings.mockResolvedValue(AI); ep.getConsents.mockResolvedValue(consents(['llm_external']));
    ep.putAISettings.mockResolvedValue(AI);
    await renderWithProviders(<AISettingsScreen {...sp({ navigation: mockNav, route: {} })} />);
    await screen.findByText('What an assistant may see');
    expect(screen.getByTestId('ai-external').props.disabled).toBeFalsy();
    await fireEvent(screen.getByTestId('ai-external'), 'valueChange', true);
    await fireEvent(screen.getByTestId('ctx-patterns'), 'valueChange', true);
    await fireEvent(screen.getByTestId('ai-personalization'), 'valueChange', false);
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.putAISettings).toHaveBeenCalledWith({ personalization_enabled: false, external_llm_allowed: true, context_allowlist: ['patterns'], chat_retention_days: 30 }));
    expect(mockNav.goBack).toHaveBeenCalled();
  });
  it('shows a server refusal and does not leave the screen', async () => {
    ep.getAISettings.mockResolvedValue(AI); ep.getConsents.mockResolvedValue(consents(['llm_external']));
    ep.putAISettings.mockRejectedValue(new ApiError(403, 'consent_required', 'Consent for llm_external is required.'));
    await renderWithProviders(<AISettingsScreen {...sp({ navigation: mockNav, route: {} })} />);
    await screen.findByText('What an assistant may see');
    await fireEvent.press(screen.getByText('Save'));
    expect(await screen.findByText('Consent for llm_external is required.')).toBeTruthy();
    expect(mockNav.goBack).not.toHaveBeenCalled();
  });
});

describe('MeScreen', () => {
  it('exports the user data through the system share sheet', async () => {
    ep.exportData.mockResolvedValue({ job_id: 'j', status: 'ready', data: { user: { email: 'asha@example.com' }, cycles: [] } });
    const share = jest.spyOn(Share, 'share').mockResolvedValue({ action: 'sharedAction' } as never);
    await renderWithProviders(<MeScreen />);
    await fireEvent.press(screen.getByText('Export my data'));
    await waitFor(() => expect(share).toHaveBeenCalled());
    expect((share.mock.calls[0]![0] as { message: string }).message).toContain('asha@example.com');
  });
  it('reports an export failure instead of failing silently', async () => {
    ep.exportData.mockRejectedValue(new ApiError(0, 'network_error', "Can't reach the server. Check your connection and try again."));
    await renderWithProviders(<MeScreen />);
    await fireEvent.press(screen.getByText('Export my data'));
    expect(await screen.findByText(/Can't reach the server/)).toBeTruthy();
  });
  it('signs out and navigates to the privacy screens', async () => {
    await renderWithProviders(<MeScreen />);
    await fireEvent.press(screen.getByText('Privacy and consent'));
    await fireEvent.press(screen.getByText('Who accessed my data'));
    expect(mockNav.navigate.mock.calls.map((c) => c[0])).toEqual(['Consents', 'AccessHistory']);
    await fireEvent.press(screen.getByText('Sign out'));
    expect(mockAuth.logout).toHaveBeenCalled();
  });
});

describe('DeleteAccountScreen', () => {
  const fill = async (password: string, confirm: string) => {
    await fireEvent.changeText(screen.getByLabelText('Your password'), password);
    await fireEvent.changeText(screen.getByLabelText('Type DELETE to confirm'), confirm);
  };
  it('does nothing unless the exact word DELETE is typed', async () => {
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    await renderWithProviders(<DeleteAccountScreen />);
    await fill('pw', 'delete');
    await fireEvent.press(screen.getByRole('button', { name: 'Delete my account' }));
    expect(await screen.findByText('Type the word DELETE in capital letters')).toBeTruthy();
    expect(alert).not.toHaveBeenCalled();
    expect(ep.deleteAccount).not.toHaveBeenCalled();
  });
  it('needs a second, explicit confirmation before erasing, then signs out', async () => {
    ep.deleteAccount.mockResolvedValue(undefined); mockAuth.logout.mockResolvedValue(undefined);
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    await renderWithProviders(<DeleteAccountScreen />);
    await fill('pw', 'DELETE');
    await fireEvent.press(screen.getByRole('button', { name: 'Delete my account' }));
    await waitFor(() => expect(alert).toHaveBeenCalled());
    expect(ep.deleteAccount).not.toHaveBeenCalled();
    (alert.mock.calls[0]![2] as { text: string; onPress?: () => void }[]).find((b) => b.text === 'Delete forever')!.onPress!();
    await waitFor(() => expect(ep.deleteAccount).toHaveBeenCalledWith('pw'));
    await waitFor(() => expect(mockAuth.logout).toHaveBeenCalled());
  });
  it('shows a wrong-password refusal and keeps the user signed in', async () => {
    ep.deleteAccount.mockRejectedValue(new ApiError(403, 'forbidden', 'Password is incorrect.'));
    const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
    await renderWithProviders(<DeleteAccountScreen />);
    await fill('wrong', 'DELETE');
    await fireEvent.press(screen.getByRole('button', { name: 'Delete my account' }));
    await waitFor(() => expect(alert).toHaveBeenCalled());
    (alert.mock.calls[0]![2] as { text: string; onPress?: () => void }[]).find((b) => b.text === 'Delete forever')!.onPress!();
    expect(await screen.findByText('Password is incorrect.')).toBeTruthy();
    expect(mockAuth.logout).not.toHaveBeenCalled();
  });
});

describe('ProfileEditScreen and AccessHistoryScreen', () => {
  it('prefills the profile and saves lists/numbers in the API shape', async () => {
    ep.getProfile.mockResolvedValue({ user_id: 'u', date_of_birth: '1999-05-04', height_cm: 162.5, weight_kg: null, typical_cycle_length: 28, contraceptive_use: null,
      conditions_self_reported: ['PCOS'], activity_level: 'moderate', dietary_prefs: ['vegetarian'], goals: [] });
    ep.putProfile.mockResolvedValue({});
    await renderWithProviders(<ProfileEditScreen {...sp({ navigation: mockNav, route: {} })} />);
    expect(await screen.findByDisplayValue('PCOS')).toBeTruthy();
    expect(screen.getByDisplayValue('162.5')).toBeTruthy();
    await fireEvent.changeText(screen.getByLabelText('Goals'), 'sleep better, more water');
    await fireEvent.press(screen.getByText('Save'));
    await waitFor(() => expect(ep.putProfile).toHaveBeenCalledWith({ date_of_birth: '1999-05-04', height_cm: 162.5, weight_kg: null, typical_cycle_length: 28,
      activity_level: 'moderate', conditions_self_reported: ['PCOS'], dietary_prefs: ['vegetarian'], goals: ['sleep better', 'more water'] }));
  });
  it('lists access history including blocked/failed attempts', async () => {
    ep.accessHistory.mockResolvedValue([
      { timestamp: '2026-03-02T10:00:00Z', action: 'read', resource: 'cycle_records', outcome: 'success', ip: null },
      { timestamp: '2026-03-02T09:00:00Z', action: 'egress_blocked', resource: 'llm', outcome: 'blocked', ip: null }]);
    await renderWithProviders(<AccessHistoryScreen />);
    expect(await screen.findByText('read · cycle records')).toBeTruthy();
    expect(screen.getByText('egress blocked · llm')).toBeTruthy();
    expect(screen.getByText(/· blocked/)).toBeTruthy();
  });
});
