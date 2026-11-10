import { MaterialCommunityIcons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';
import { View } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';

import { useAuth } from '@/auth/AuthContext';
import { Loading } from '@/components/ui';
import { ForgotPasswordScreen, LoginScreen, RegisterScreen, ResetPasswordScreen } from '@/screens/auth/AuthScreens';
import { CycleFormScreen, CycleScreen } from '@/screens/cycle/CycleScreens';
import { HomeScreen } from '@/screens/dashboard/HomeScreen';
import { LifestyleFormScreen, LogScreen, MoodFormScreen, SymptomFormScreen } from '@/screens/log/LogScreens';
import { AccessHistoryScreen, AISettingsScreen, ConsentsScreen, DeleteAccountScreen, MeScreen, ProfileEditScreen } from '@/screens/me/MeScreens';
import { OnboardingScreen } from '@/screens/onboarding/OnboardingScreen';

import type { RootParamList, TabParamList } from './types';

const Stack = createNativeStackNavigator<RootParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

type IconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];
const TAB_ICONS: Record<keyof TabParamList, IconName> = { Home: 'home-heart', Cycle: 'calendar-heart', Log: 'plus-circle-outline', Me: 'account-circle-outline' };

function Tabs() {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name={TAB_ICONS[route.name]} color={color} size={size} />,
      tabBarLabelStyle: { fontSize: 12 },
    })}>
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Today', tabBarAccessibilityLabel: 'Today' }} />
      <Tab.Screen name="Cycle" component={CycleScreen} options={{ title: 'Cycle' }} />
      <Tab.Screen name="Log" component={LogScreen} options={{ title: 'Log' }} />
      <Tab.Screen name="Me" component={MeScreen} options={{ title: 'Me' }} />
    </Tab.Navigator>
  );
}

function Splash() {
  const theme = useTheme();
  return <View style={{ flex: 1, backgroundColor: theme.colors.background, justifyContent: 'center' }}><Loading label="Starting" /></View>;
}

function Unreachable() {
  const { retryBootstrap } = useAuth();
  const theme = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background, justifyContent: 'center', padding: 24, gap: 12 }} accessibilityRole="alert">
      <Text variant="titleLarge">You are offline</Text>
      <Text>We cannot reach the server. Your session is kept, so you can try again when you are connected.</Text>
      <Button mode="contained" onPress={retryBootstrap}>Try again</Button>
    </View>
  );
}

export function RootNavigator({ onboardingDone, onFinishOnboarding }: { onboardingDone: boolean; onFinishOnboarding: () => void }) {
  const { status } = useAuth();
  if (status === 'loading') return <Splash />;
  if (status === 'unreachable') return <Unreachable />;
  if (status === 'signedOut') {
    if (!onboardingDone) return <OnboardingScreen onDone={onFinishOnboarding} />;
    return (
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'Sign in' }} />
        <Stack.Screen name="Register" component={RegisterScreen} options={{ title: 'Create account' }} />
        <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} options={{ title: 'Forgot password' }} />
        <Stack.Screen name="ResetPassword" component={ResetPasswordScreen} options={{ title: 'Reset password' }} />
      </Stack.Navigator>
    );
  }
  return (
    <Stack.Navigator>
      <Stack.Screen name="Tabs" component={Tabs} options={{ headerShown: false }} />
      <Stack.Screen name="CycleForm" component={CycleFormScreen} options={{ title: 'Period' }} />
      <Stack.Screen name="SymptomForm" component={SymptomFormScreen} options={{ title: 'Symptom' }} />
      <Stack.Screen name="LifestyleForm" component={LifestyleFormScreen} options={{ title: 'Sleep and lifestyle' }} />
      <Stack.Screen name="MoodForm" component={MoodFormScreen} options={{ title: 'Mood' }} />
      <Stack.Screen name="ProfileEdit" component={ProfileEditScreen} options={{ title: 'Health profile' }} />
      <Stack.Screen name="Consents" component={ConsentsScreen} options={{ title: 'Privacy and consent' }} />
      <Stack.Screen name="AISettings" component={AISettingsScreen} options={{ title: 'AI and data sharing' }} />
      <Stack.Screen name="AccessHistory" component={AccessHistoryScreen} options={{ title: 'Access history' }} />
      <Stack.Screen name="DeleteAccount" component={DeleteAccountScreen} options={{ title: 'Delete account' }} />
    </Stack.Navigator>
  );
}
