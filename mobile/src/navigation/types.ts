import type { NavigatorScreenParams } from '@react-navigation/native';

export type TabParamList = { Home: undefined; Cycle: undefined; Log: undefined; Me: undefined };

export type RootParamList = {
  // signed-out
  Onboarding: undefined;
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  ResetPassword: { token?: string } | undefined;
  // signed-in
  Tabs: NavigatorScreenParams<TabParamList> | undefined;
  CycleForm: { cycleId?: string } | undefined;
  SymptomForm: undefined;
  LifestyleForm: { date?: string } | undefined;
  MoodForm: undefined;
  ProfileEdit: undefined;
  Consents: undefined;
  AISettings: undefined;
  AccessHistory: undefined;
  DeleteAccount: undefined;
};
