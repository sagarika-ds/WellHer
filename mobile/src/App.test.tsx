import AsyncStorage from '@react-native-async-storage/async-storage';
import { render, screen, waitFor } from '@testing-library/react-native';
import React from 'react';

import App from './App';

// The real provider renders nothing until native code reports insets; use the library's official Jest mock.
jest.mock('react-native-safe-area-context', () => require('react-native-safe-area-context/jest/mock').default);

it('boots to onboarding on first launch (no stored session, no network needed)', async () => {
  await AsyncStorage.clear();
  await render(<App />);
  await waitFor(() => expect(screen.getByText('Understand your body, gently')).toBeTruthy());
});

it('skips onboarding once completed and lands on sign-in', async () => {
  await AsyncStorage.setItem('onboarding.done', '1');
  await render(<App />);
  await waitFor(() => expect(screen.getByText('Welcome back')).toBeTruthy());
});
