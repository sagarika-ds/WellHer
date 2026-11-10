import { z } from 'zod';

import { SYMPTOM_CODES } from '@/types/api';

import { isISODate } from './dates';

const isoDate = z.string().refine(isISODate, 'Use the format YYYY-MM-DD');
const score = z.number().int().min(1).max(5);
const optionalNumber = (min: number, max: number, label: string) =>
  z.preprocess(
    (v) => (v === '' || v === null || v === undefined || (typeof v === 'number' && Number.isNaN(v)) ? undefined : Number(v)),
    z.number({ error: `${label} must be a number` }).min(min, `${label} must be at least ${min}`).max(max, `${label} must be at most ${max}`).optional(),
  );

export const loginSchema = z.object({
  email: z.string().trim().min(1, 'Enter your email').pipe(z.email('Enter a valid email address')),
  password: z.string().min(1, 'Enter your password'),
});

export const registerSchema = z
  .object({
    displayName: z.string().trim().min(1, 'Enter a name').max(100),
    email: z.string().trim().min(1, 'Enter your email').pipe(z.email('Enter a valid email address')),
    password: z.string().min(12, 'Use at least 12 characters').max(128),
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' })
  .refine((v) => { const local = v.email.split('@')[0]?.toLowerCase() ?? ''; return local.length < 4 || !v.password.toLowerCase().includes(local); },
    { path: ['password'], message: 'Password must not contain your email name' });

export const forgotSchema = z.object({ email: z.string().trim().min(1, 'Enter your email').pipe(z.email('Enter a valid email address')) });

export const resetSchema = z
  .object({ token: z.string().trim().min(20, 'Paste the full code from the email'), password: z.string().min(12, 'Use at least 12 characters').max(128), confirm: z.string() })
  .refine((v) => v.password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' });

export const cycleSchema = z
  .object({ start_date: isoDate, end_date: z.union([isoDate, z.literal('')]), flow_intensity: score.optional(), notes: z.string().max(2000).optional() })
  .refine((v) => v.end_date === '' || v.end_date >= v.start_date, { path: ['end_date'], message: 'End date cannot be before the start date' })
  .refine((v) => v.end_date === '' || (new Date(v.end_date).getTime() - new Date(v.start_date).getTime()) / 86_400_000 <= 21,
    { path: ['end_date'], message: 'A period longer than 21 days looks like a mistake' });

export const symptomSchema = z.object({ symptom_code: z.enum(SYMPTOM_CODES, { error: 'Choose a symptom' }), severity: score });

export const lifestyleSchema = z.object({
  date: isoDate,
  sleep_hours: optionalNumber(0, 24, 'Sleep'),
  sleep_quality: score.optional(),
  activity_minutes: optionalNumber(0, 1440, 'Activity'),
  water_ml: optionalNumber(0, 20000, 'Water'),
  stress_level: score.optional(),
  nutrition_notes: z.string().max(2000).optional(),
});

export const moodSchema = z.object({ mood_score: score, tags: z.array(z.string()).max(10) });

export const profileSchema = z.object({
  date_of_birth: z.union([isoDate, z.literal('')]),
  height_cm: optionalNumber(50, 250, 'Height'),
  weight_kg: optionalNumber(20, 400, 'Weight'),
  typical_cycle_length: optionalNumber(15, 90, 'Cycle length'),
  activity_level: z.enum(['sedentary', 'light', 'moderate', 'active']).optional(),
  conditions: z.string().max(400),
  dietary_prefs: z.string().max(400),
  goals: z.string().max(400),
});

/** Comma-separated text <-> list, trimmed, empties dropped. */
export const splitList = (s: string): string[] => s.split(',').map((x) => x.trim()).filter(Boolean);

export const deleteAccountSchema = z.object({
  password: z.string().min(1, 'Enter your password'),
  confirm: z.literal('DELETE', { error: 'Type the word DELETE in capital letters' }),
});
