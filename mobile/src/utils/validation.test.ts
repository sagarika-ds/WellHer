import { cycleSchema, deleteAccountSchema, lifestyleSchema, loginSchema, moodSchema, profileSchema, registerSchema, resetSchema, splitList, symptomSchema } from './validation';

const msgs = (r: { success: boolean; error?: { issues: { message: string }[] } }) => (r.success ? [] : r.error!.issues.map((i) => i.message));

describe('auth schemas', () => {
  it('login requires a valid email and a password', () => {
    expect(loginSchema.safeParse({ email: ' a@b.co ', password: 'x' }).success).toBe(true);
    expect(msgs(loginSchema.safeParse({ email: '', password: '' }))).toEqual(expect.arrayContaining(['Enter your email', 'Enter your password']));
    expect(msgs(loginSchema.safeParse({ email: 'nope', password: 'x' }))).toContain('Enter a valid email address');
  });
  const base = { displayName: 'Asha', email: 'asha.rao@example.com', password: 'Violet-Harbor-42', confirm: 'Violet-Harbor-42' };
  it('register mirrors the backend password rules', () => {
    expect(registerSchema.safeParse(base).success).toBe(true);
    expect(msgs(registerSchema.safeParse({ ...base, password: 'short', confirm: 'short' }))).toContain('Use at least 12 characters');
    expect(msgs(registerSchema.safeParse({ ...base, confirm: 'different-password-1' }))).toContain('Passwords do not match');
    expect(msgs(registerSchema.safeParse({ ...base, email: 'janedoe@example.com', password: 'janedoe-is-me-123', confirm: 'janedoe-is-me-123' }))).toContain('Password must not contain your email name');
    expect(msgs(registerSchema.safeParse({ ...base, displayName: '   ' }))).toContain('Enter a name');
  });
  it('reset needs the full code and matching passwords', () => {
    expect(resetSchema.safeParse({ token: 'x'.repeat(40), password: 'Violet-Harbor-42', confirm: 'Violet-Harbor-42' }).success).toBe(true);
    expect(msgs(resetSchema.safeParse({ token: 'short', password: 'Violet-Harbor-42', confirm: 'Violet-Harbor-42' }))).toContain('Paste the full code from the email');
  });
});

describe('record schemas', () => {
  it('cycle: end not before start, at most 21 days', () => {
    expect(cycleSchema.safeParse({ start_date: '2026-03-01', end_date: '' }).success).toBe(true);
    expect(msgs(cycleSchema.safeParse({ start_date: '2026-03-05', end_date: '2026-03-01' }))).toContain('End date cannot be before the start date');
    expect(msgs(cycleSchema.safeParse({ start_date: '2026-03-01', end_date: '2026-04-15' }))).toContain('A period longer than 21 days looks like a mistake');
    expect(msgs(cycleSchema.safeParse({ start_date: '2026-02-30', end_date: '' }))).toContain('Use the format YYYY-MM-DD');
    expect(cycleSchema.safeParse({ start_date: '2026-03-01', end_date: '', flow_intensity: 6 }).success).toBe(false);
  });
  it('lifestyle: empty numeric fields become undefined; ranges enforced', () => {
    const ok = lifestyleSchema.parse({ date: '2026-03-01', sleep_hours: '', activity_minutes: '', water_ml: '' });
    expect(ok.sleep_hours).toBeUndefined();
    expect(lifestyleSchema.parse({ date: '2026-03-01', sleep_hours: '7.5' }).sleep_hours).toBe(7.5);
    expect(msgs(lifestyleSchema.safeParse({ date: '2026-03-01', sleep_hours: '25' }))).toContain('Sleep must be at most 24');
    expect(lifestyleSchema.safeParse({ date: '2026-03-01', water_ml: '-5' }).success).toBe(false);
    expect(lifestyleSchema.safeParse({ date: '2026-03-01', sleep_hours: 'abc' }).success).toBe(false);
  });
  it('symptom: code must be in the shared ontology, severity 1-5', () => {
    expect(symptomSchema.safeParse({ symptom_code: 'headache', severity: 3 }).success).toBe(true);
    expect(symptomSchema.safeParse({ symptom_code: 'made_up', severity: 3 }).success).toBe(false);
    expect(symptomSchema.safeParse({ symptom_code: 'headache', severity: 0 }).success).toBe(false);
  });
  it('mood: score required', () => {
    expect(moodSchema.safeParse({ mood_score: 4, tags: ['calm'] }).success).toBe(true);
    expect(moodSchema.safeParse({ tags: [] }).success).toBe(false);
  });
  it('profile ranges and list splitting', () => {
    const base = { date_of_birth: '', conditions: '', dietary_prefs: '', goals: '' };
    expect(profileSchema.safeParse({ ...base, height_cm: '10' }).success).toBe(false);
    expect(profileSchema.safeParse({ ...base, typical_cycle_length: '28' }).success).toBe(true);
    expect(splitList(' vegetarian, ,low sugar ,')).toEqual(['vegetarian', 'low sugar']);
  });
  it('account deletion needs the exact word DELETE', () => {
    expect(deleteAccountSchema.safeParse({ password: 'x', confirm: 'DELETE' }).success).toBe(true);
    expect(deleteAccountSchema.safeParse({ password: 'x', confirm: 'delete' }).success).toBe(false);
    expect(deleteAccountSchema.safeParse({ password: '', confirm: 'DELETE' }).success).toBe(false);
  });
});
