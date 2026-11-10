import type { components } from './api.generated';

/** Friendly aliases over the types generated from the backend's real OpenAPI document. */
type S = components['schemas'];

export type UserOut = S['UserOut'];
export type TokenPair = S['TokenPair'];
export type RegisterRequest = S['RegisterRequest'];
export type ConsentChoice = S['ConsentChoice'];
export type ConsentOut = S['ConsentOut'];
export type ProfileIn = S['ProfileIn'];
export type ProfileOut = S['ProfileOut'];
export type CycleIn = S['CycleIn'];
export type CycleOut = S['CycleOut'];
export type CycleStats = S['CycleStats'];
export type SymptomIn = S['SymptomIn'];
export type SymptomOut = S['SymptomOut'];
export type LifestyleIn = S['LifestyleIn'];
export type LifestyleOut = S['LifestyleOut'];
export type LifestyleSummary = S['LifestyleSummary'];
export type MoodIn = S['MoodIn'];
export type MoodOut = S['MoodOut'];
export type AISettings = S['AISettingsOut'];
export type AISettingsIn = S['AISettingsIn'];
export type AccessHistoryItem = S['AccessHistoryItem'];
export type ExportOut = S['ExportOut'];

export type ConsentPurpose = ConsentChoice['purpose'];
export const CONSENT_PURPOSES: ConsentPurpose[] = ['health_tracking', 'ml_processing', 'llm_external', 'analytics'];

/** Mirrors backend app/core/ontology.py. Extended (multilingual) in a later milestone. */
export const SYMPTOM_CODES = [
  'fatigue', 'headache', 'cramps', 'bloating', 'nausea', 'back_pain', 'pelvic_pain', 'breast_tenderness',
  'mood_swings', 'irritability', 'anxiety', 'low_mood', 'insomnia', 'acne', 'dizziness', 'hot_flashes',
  'appetite_change', 'cravings', 'joint_pain', 'muscle_pain', 'spotting', 'heavy_bleeding', 'constipation',
  'diarrhea',
] as const;
export type SymptomCode = (typeof SYMPTOM_CODES)[number];

export const MOOD_TAGS = ['calm', 'happy', 'energetic', 'focused', 'tired', 'anxious', 'irritable', 'sad'] as const;
