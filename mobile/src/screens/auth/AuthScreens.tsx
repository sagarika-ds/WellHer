import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { KeyboardAvoidingView, Platform, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import type { z } from 'zod';

import { errorMessage } from '@/api/errors';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/auth/AuthContext';
import { SwitchRow, TextField } from '@/components/forms';
import { FormError, InfoCard, Screen } from '@/components/ui';
import { DISCLAIMER } from '@/config';
import type { RootParamList } from '@/navigation/types';
import { CONSENT_PURPOSES, type ConsentPurpose } from '@/types/api';
import { forgotSchema, loginSchema, registerSchema, resetSchema } from '@/utils/validation';

type Props<T extends keyof RootParamList> = NativeStackScreenProps<RootParamList, T>;

export function LoginScreen({ navigation }: Props<'Login'>) {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<z.infer<typeof loginSchema>>({ resolver: zodResolver(loginSchema), defaultValues: { email: '', password: '' } });
  const submit = handleSubmit(async (v) => {
    setError(null);
    try { await login(v.email, v.password); } catch (e) { setError(errorMessage(e)); }
  });
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen>
        <Text variant="headlineMedium" accessibilityRole="header">Welcome back</Text>
        <TextField control={control} name="email" label="Email" keyboardType="email-address" autoComplete="email" />
        <TextField control={control} name="password" label="Password" secure autoComplete="password" />
        {error ? <FormError error={new Error(error)} /> : null}
        <Button mode="contained" onPress={() => void submit()} loading={isSubmitting} disabled={isSubmitting}>Sign in</Button>
        <Button onPress={() => navigation.navigate('ForgotPassword')}>Forgot password?</Button>
        <Button onPress={() => navigation.navigate('Register')}>Create an account</Button>
        <Text variant="bodySmall">{DISCLAIMER}</Text>
      </Screen>
    </KeyboardAvoidingView>
  );
}

const CONSENT_COPY: Record<ConsentPurpose, { label: string; description: string }> = {
  health_tracking: { label: 'Health tracking', description: 'Store and show the cycles, symptoms, sleep and mood you log. Needed to use the tracking features.' },
  ml_processing: { label: 'Insights from my records', description: 'Allow analysis of your records to produce insights. Insight features arrive in a later version.' },
  llm_external: { label: 'External AI providers', description: 'Allow de-identified text to be sent to an outside AI service. Off unless you choose it.' },
  analytics: { label: 'Anonymous usage statistics', description: 'Help improve the app. Never includes your health records.' },
};

export function RegisterScreen({ navigation }: Props<'Register'>) {
  const { register } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [consents, setConsents] = useState<Record<ConsentPurpose, boolean>>({ health_tracking: false, ml_processing: false, llm_external: false, analytics: false });
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<z.infer<typeof registerSchema>>({
    resolver: zodResolver(registerSchema), defaultValues: { displayName: '', email: '', password: '', confirm: '' },
  });
  const submit = handleSubmit(async (v) => {
    setError(null);
    try {
      await register({ email: v.email, password: v.password, displayName: v.displayName,
        consents: CONSENT_PURPOSES.map((purpose) => ({ purpose, granted: consents[purpose] })) });
    } catch (e) { setError(errorMessage(e)); }
  });
  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen>
        <Text variant="headlineMedium" accessibilityRole="header">Create your account</Text>
        <TextField control={control} name="displayName" label="Name" autoComplete="name" />
        <TextField control={control} name="email" label="Email" keyboardType="email-address" autoComplete="email" />
        <TextField control={control} name="password" label="Password" secure autoComplete="new-password" hint="At least 12 characters" />
        <TextField control={control} name="confirm" label="Confirm password" secure autoComplete="new-password" />
        <InfoCard>
          <Text variant="titleMedium" accessibilityRole="header">Your choices</Text>
          <Text variant="bodySmall">Everything is off until you turn it on. You can change any of these later in Privacy settings.</Text>
          {CONSENT_PURPOSES.map((p) => (
            <SwitchRow key={p} label={CONSENT_COPY[p].label} description={CONSENT_COPY[p].description} value={consents[p]}
              onValueChange={(v) => setConsents((c) => ({ ...c, [p]: v }))} testID={`consent-${p}`} />
          ))}
        </InfoCard>
        {error ? <FormError error={new Error(error)} /> : null}
        <Button mode="contained" onPress={() => void submit()} loading={isSubmitting} disabled={isSubmitting}>Create account</Button>
        <Button onPress={() => navigation.navigate('Login')}>I already have an account</Button>
      </Screen>
    </KeyboardAvoidingView>
  );
}

export function ForgotPasswordScreen({ navigation }: Props<'ForgotPassword'>) {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<z.infer<typeof forgotSchema>>({ resolver: zodResolver(forgotSchema), defaultValues: { email: '' } });
  const submit = handleSubmit(async (v) => {
    setError(null);
    try { await endpoints.forgotPassword(v.email); setSent(true); } catch (e) { setError(errorMessage(e)); }
  });
  return (
    <Screen>
      <Text variant="headlineMedium" accessibilityRole="header">Reset your password</Text>
      {sent ? (
        <InfoCard tone="soft">
          <Text accessibilityRole="alert">If an account exists for that email, a reset message has been sent. Check your inbox.</Text>
          <Button mode="contained" onPress={() => navigation.navigate('ResetPassword')}>I have a reset code</Button>
        </InfoCard>
      ) : (
        <>
          <TextField control={control} name="email" label="Email" keyboardType="email-address" autoComplete="email" />
          {error ? <FormError error={new Error(error)} /> : null}
          <Button mode="contained" onPress={() => void submit()} loading={isSubmitting} disabled={isSubmitting}>Send reset message</Button>
          <Button onPress={() => navigation.navigate('ResetPassword')}>I already have a code</Button>
        </>
      )}
    </Screen>
  );
}

export function ResetPasswordScreen({ navigation, route }: Props<'ResetPassword'>) {
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<z.infer<typeof resetSchema>>({
    resolver: zodResolver(resetSchema), defaultValues: { token: route.params?.token ?? '', password: '', confirm: '' },
  });
  const submit = handleSubmit(async (v) => {
    setError(null);
    try { await endpoints.resetPassword(v.token, v.password); setDone(true); } catch (e) { setError(errorMessage(e)); }
  });
  return (
    <Screen>
      <Text variant="headlineMedium" accessibilityRole="header">Choose a new password</Text>
      {done ? (
        <View style={{ gap: 12 }}>
          <Text accessibilityRole="alert">Your password was changed. You can now sign in.</Text>
          <Button mode="contained" onPress={() => navigation.navigate('Login')}>Go to sign in</Button>
        </View>
      ) : (
        <>
          <TextField control={control} name="token" label="Reset code" />
          <TextField control={control} name="password" label="New password" secure autoComplete="new-password" hint="At least 12 characters" />
          <TextField control={control} name="confirm" label="Confirm new password" secure autoComplete="new-password" />
          {error ? <FormError error={new Error(error)} /> : null}
          <Button mode="contained" onPress={() => void submit()} loading={isSubmitting} disabled={isSubmitting}>Change password</Button>
        </>
      )}
    </Screen>
  );
}
