import { NavigationContainer } from '@react-navigation/native';
import { fireEvent, screen } from '@testing-library/react-native';
import React from 'react';

import { renderWithProviders } from '@/__tests__/testUtils';
import { ApiError } from '@/api/errors';

import { RootNavigator } from './RootNavigator';

const mockAuth: { status: string; user: unknown; retryBootstrap: jest.Mock; login: jest.Mock; register: jest.Mock; logout: jest.Mock } =
  { status: 'loading', user: null, retryBootstrap: jest.fn(), login: jest.fn(), register: jest.fn(), logout: jest.fn() };
jest.mock('@/auth/AuthContext', () => ({ useAuth: () => mockAuth }));
jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
import { endpoints, type Endpoints } from '@/api/endpoints';
const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;

const mount = (onboardingDone: boolean, onFinish = jest.fn()) =>
  renderWithProviders(<NavigationContainer><RootNavigator onboardingDone={onboardingDone} onFinishOnboarding={onFinish} /></NavigationContainer>);

beforeEach(() => { mockAuth.retryBootstrap.mockReset(); });

it('shows a loading state while the session is being restored', async () => {
  mockAuth.status = 'loading';
  await mount(true);
  expect(screen.getByLabelText('Starting')).toBeTruthy();
});

it('offline at start: explains, keeps the session, and offers retry', async () => {
  mockAuth.status = 'unreachable';
  await mount(true);
  expect(screen.getByText('You are offline')).toBeTruthy();
  await fireEvent.press(screen.getByText('Try again'));
  expect(mockAuth.retryBootstrap).toHaveBeenCalled();
});

it('signed out + first launch: onboarding, then it hands over via the callback', async () => {
  mockAuth.status = 'signedOut';
  const onFinish = jest.fn();
  await mount(false, onFinish);
  expect(screen.getByText('Awareness, not diagnosis')).toBeTruthy();
  await fireEvent.press(screen.getByText('Skip'));
  expect(onFinish).toHaveBeenCalled();
});

it('signed out after onboarding: the sign-in screen, and no health screens reachable', async () => {
  mockAuth.status = 'signedOut';
  await mount(true);
  expect(screen.getByText('Welcome back')).toBeTruthy();
  expect(screen.queryByText('Today')).toBeNull();
});

it('signed in: the four tabs are shown (health data still gated by consent from the server)', async () => {
  mockAuth.status = 'signedIn';
  mockAuth.user = { id: 'u', email: 'a@b.co', display_name: 'Asha', role: 'user' };
  const consent = new ApiError(403, 'consent_required', 'Consent for health_tracking is required.');
  (['listCycles', 'cycleStats', 'lifestyleSummary', 'listLifestyle', 'listMood', 'listSymptoms'] as (keyof Endpoints)[]).forEach((k) => ep[k].mockRejectedValue(consent));
  await mount(true);
  for (const tab of ['Today', 'Cycle', 'Log', 'Me']) expect(screen.getAllByText(tab).length).toBeGreaterThan(0);
  expect(await screen.findByText('Health tracking is turned off')).toBeTruthy();
  expect(screen.queryByText('Welcome back')).toBeNull();
});
