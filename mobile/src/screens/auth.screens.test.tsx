import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import React from 'react';

import { navMock, renderWithProviders, sp } from '@/__tests__/testUtils';
import { ApiError } from '@/api/errors';

import { ForgotPasswordScreen, LoginScreen, RegisterScreen, ResetPasswordScreen } from './auth/AuthScreens';
import { OnboardingScreen } from './onboarding/OnboardingScreen';

const mockAuth = { login: jest.fn(), register: jest.fn(), logout: jest.fn(), user: null, status: 'signedOut', retryBootstrap: jest.fn() };
jest.mock('@/auth/AuthContext', () => ({ useAuth: () => mockAuth }));
jest.mock('@/api/endpoints', () => ({ endpoints: new Proxy({}, { get: (t: Record<string, jest.Mock>, k: string) => (t[k] ??= jest.fn()) }), ROUTES: {} }));
import { endpoints, type Endpoints } from '@/api/endpoints';
const ep = endpoints as unknown as Record<keyof Endpoints, jest.Mock>;

const type = (label: string, text: string) => fireEvent.changeText(screen.getByLabelText(label), text);
beforeEach(() => jest.clearAllMocks());

describe('LoginScreen', () => {
  it('validates before calling the server', async () => {
    await renderWithProviders(<LoginScreen {...sp({ navigation: navMock() })} />);
    await fireEvent.press(screen.getByText('Sign in'));
    expect(await screen.findByText('Enter your email')).toBeTruthy();
    expect(screen.getByText('Enter your password')).toBeTruthy();
    expect(mockAuth.login).not.toHaveBeenCalled();
  });
  it('submits trimmed credentials', async () => {
    mockAuth.login.mockResolvedValue(undefined);
    await renderWithProviders(<LoginScreen {...sp({ navigation: navMock() })} />);
    await type('Email', '  asha@example.com ');
    await type('Password', 'secret-pass');
    await fireEvent.press(screen.getByText('Sign in'));
    await waitFor(() => expect(mockAuth.login).toHaveBeenCalledWith('asha@example.com', 'secret-pass'));
  });
  it('shows the server message (and not a stack or code) when sign-in fails', async () => {
    mockAuth.login.mockRejectedValue(new ApiError(401, 'unauthenticated', 'Invalid email or password.'));
    await renderWithProviders(<LoginScreen {...sp({ navigation: navMock() })} />);
    await type('Email', 'a@b.co'); await type('Password', 'x');
    await fireEvent.press(screen.getByText('Sign in'));
    expect(await screen.findByText('Invalid email or password.')).toBeTruthy();
  });
  it('links to registration and password reset', async () => {
    const navigation = navMock();
    await renderWithProviders(<LoginScreen {...sp({ navigation })} />);
    await fireEvent.press(screen.getByText('Forgot password?'));
    await fireEvent.press(screen.getByText('Create an account'));
    expect(navigation.navigate.mock.calls.map((c) => c[0])).toEqual(['ForgotPassword', 'Register']);
  });
});

describe('RegisterScreen', () => {
  const fill = async (over: Partial<Record<string, string>> = {}) => {
    const v = { Name: 'Asha', Email: 'asha@example.com', Password: 'Violet-Harbor-42', 'Confirm password': 'Violet-Harbor-42', ...over };
    for (const [k, val] of Object.entries(v)) await type(k, val);
  };
  it('starts with every consent OFF (opt-in, no pre-ticked boxes)', async () => {
    await renderWithProviders(<RegisterScreen {...sp({ navigation: navMock() })} />);
    for (const p of ['health_tracking', 'ml_processing', 'llm_external', 'analytics']) expect(screen.getByTestId(`consent-${p}`).props.value).toBe(false);
  });
  it('sends exactly the consents the user switched on', async () => {
    mockAuth.register.mockResolvedValue(undefined);
    await renderWithProviders(<RegisterScreen {...sp({ navigation: navMock() })} />);
    await fill();
    await fireEvent(screen.getByTestId('consent-health_tracking'), 'valueChange', true);
    await fireEvent.press(screen.getByText('Create account'));
    await waitFor(() => expect(mockAuth.register).toHaveBeenCalled());
    expect(mockAuth.register.mock.calls[0]![0]).toEqual({
      email: 'asha@example.com', password: 'Violet-Harbor-42', displayName: 'Asha',
      consents: [{ purpose: 'health_tracking', granted: true }, { purpose: 'ml_processing', granted: false }, { purpose: 'llm_external', granted: false }, { purpose: 'analytics', granted: false }],
    });
  });
  it('blocks mismatched or short passwords locally', async () => {
    await renderWithProviders(<RegisterScreen {...sp({ navigation: navMock() })} />);
    await fill({ 'Confirm password': 'something-else-123' });
    await fireEvent.press(screen.getByText('Create account'));
    expect(await screen.findByText('Passwords do not match')).toBeTruthy();
    await fill({ Password: 'short', 'Confirm password': 'short' });
    await fireEvent.press(screen.getByText('Create account'));
    expect(await screen.findByText('Use at least 12 characters')).toBeTruthy();
    expect(mockAuth.register).not.toHaveBeenCalled();
  });
  it('shows a duplicate-email conflict from the server', async () => {
    mockAuth.register.mockRejectedValue(new ApiError(409, 'conflict', 'An account with this email already exists.'));
    await renderWithProviders(<RegisterScreen {...sp({ navigation: navMock() })} />);
    await fill();
    await fireEvent.press(screen.getByText('Create account'));
    expect(await screen.findByText('An account with this email already exists.')).toBeTruthy();
  });
});

describe('password reset screens', () => {
  it('forgot password gives the same neutral confirmation (no account enumeration)', async () => {
    ep.forgotPassword.mockResolvedValue(undefined);
    await renderWithProviders(<ForgotPasswordScreen {...sp({ navigation: navMock() })} />);
    await type('Email', 'anyone@example.com');
    await fireEvent.press(screen.getByText('Send reset message'));
    expect(await screen.findByText(/If an account exists for that email/)).toBeTruthy();
    expect(ep.forgotPassword).toHaveBeenCalledWith('anyone@example.com');
  });
  it('reset sends the code and new password, and reports an invalid code', async () => {
    ep.resetPassword.mockRejectedValueOnce(new ApiError(400, 'invalid_reset_token', 'This reset link is invalid or has expired.'));
    await renderWithProviders(<ResetPasswordScreen {...sp({ navigation: navMock(), route: { params: undefined } })} />);
    await type('Reset code', 'x'.repeat(30)); await type('New password', 'Violet-Harbor-42'); await type('Confirm new password', 'Violet-Harbor-42');
    await fireEvent.press(screen.getByText('Change password'));
    expect(await screen.findByText('This reset link is invalid or has expired.')).toBeTruthy();
    ep.resetPassword.mockResolvedValueOnce(undefined);
    await fireEvent.press(screen.getByText('Change password'));
    expect(await screen.findByText(/Your password was changed/)).toBeTruthy();
    expect(ep.resetPassword).toHaveBeenLastCalledWith('x'.repeat(30), 'Violet-Harbor-42');
  });
});

describe('OnboardingScreen', () => {
  it('states the wellness-not-diagnosis position and can be skipped', async () => {
    const onDone = jest.fn();
    await renderWithProviders(<OnboardingScreen onDone={onDone} />);
    expect(screen.getByText('Awareness, not diagnosis')).toBeTruthy();
    expect(screen.getByText(/does not diagnose, treat or replace/)).toBeTruthy();
    await fireEvent.press(screen.getByText('Skip'));
    expect(onDone).toHaveBeenCalled();
  });
});
