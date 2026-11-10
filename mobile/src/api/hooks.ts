import { useMutation, useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query';

import type { AISettingsIn, ConsentPurpose, CycleIn, LifestyleIn, MoodIn, ProfileIn, SymptomIn } from '@/types/api';

import { endpoints, type DateRange } from './endpoints';

export const keys = {
  cycles: ['cycles'] as const, cycleStats: ['cycleStats'] as const,
  symptoms: ['symptoms'] as const, lifestyle: ['lifestyle'] as const, lifestyleSummary: ['lifestyleSummary'] as const,
  mood: ['mood'] as const, profile: ['profile'] as const, consents: ['consents'] as const,
  ai: ['aiSettings'] as const, history: ['accessHistory'] as const,
};

export const useCycles = (p: DateRange = { limit: 100 }) => useQuery({ queryKey: [...keys.cycles, p], queryFn: () => endpoints.listCycles(p) });
export const useCycleStats = () => useQuery({ queryKey: keys.cycleStats, queryFn: endpoints.cycleStats });
export const useSymptoms = (p: DateRange = { limit: 10 }) => useQuery({ queryKey: [...keys.symptoms, p], queryFn: () => endpoints.listSymptoms(p) });
export const useLifestyle = (p: DateRange = { limit: 7 }) => useQuery({ queryKey: [...keys.lifestyle, p], queryFn: () => endpoints.listLifestyle(p) });
export const useLifestyleSummary = (days = 7) => useQuery({ queryKey: [...keys.lifestyleSummary, days], queryFn: () => endpoints.lifestyleSummary(days) });
export const useMood = (p: DateRange = { limit: 7 }) => useQuery({ queryKey: [...keys.mood, p], queryFn: () => endpoints.listMood(p) });
export const useProfile = () => useQuery({ queryKey: keys.profile, queryFn: endpoints.getProfile });
export const useConsents = () => useQuery({ queryKey: keys.consents, queryFn: endpoints.getConsents });
export const useAISettings = () => useQuery({ queryKey: keys.ai, queryFn: endpoints.getAISettings });
export const useAccessHistory = () => useQuery({ queryKey: keys.history, queryFn: () => endpoints.accessHistory(100, 0) });

function useInvalidatingMutation<TVars, TData>(fn: (v: TVars) => Promise<TData>, invalidate: QueryKey[]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: async () => { await Promise.all(invalidate.map((queryKey) => qc.invalidateQueries({ queryKey }))); },
  });
}

export const useCreateCycle = () => useInvalidatingMutation((b: CycleIn) => endpoints.createCycle(b), [keys.cycles, keys.cycleStats]);
export const useUpdateCycle = () => useInvalidatingMutation((v: { id: string; body: CycleIn }) => endpoints.updateCycle(v.id, v.body), [keys.cycles, keys.cycleStats]);
export const useDeleteCycle = () => useInvalidatingMutation((id: string) => endpoints.deleteCycle(id), [keys.cycles, keys.cycleStats]);
export const useCreateSymptom = () => useInvalidatingMutation((b: SymptomIn) => endpoints.createSymptom(b), [keys.symptoms]);
export const useDeleteSymptom = () => useInvalidatingMutation((id: string) => endpoints.deleteSymptom(id), [keys.symptoms]);
export const useSaveLifestyle = () =>
  useInvalidatingMutation(
    (v: { existingId?: string; body: LifestyleIn }) => (v.existingId ? endpoints.updateLifestyle(v.existingId, v.body) : endpoints.createLifestyle(v.body)),
    [keys.lifestyle, keys.lifestyleSummary],
  );
export const useCreateMood = () => useInvalidatingMutation((b: MoodIn) => endpoints.createMood(b), [keys.mood]);
export const useSaveProfile = () => useInvalidatingMutation((b: ProfileIn) => endpoints.putProfile(b), [keys.profile]);
export const useSetConsent = () =>
  useInvalidatingMutation(
    (v: { purpose: ConsentPurpose; granted: boolean }) => endpoints.setConsent(v.purpose, v.granted),
    // changing consent changes what every health screen is allowed to load
    [keys.consents, keys.cycles, keys.cycleStats, keys.symptoms, keys.lifestyle, keys.lifestyleSummary, keys.mood],
  );
export const useSaveAISettings = () => useInvalidatingMutation((b: AISettingsIn) => endpoints.putAISettings(b), [keys.ai]);
