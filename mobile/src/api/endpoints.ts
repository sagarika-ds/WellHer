import type { AxiosInstance } from 'axios';

import type {
  AISettings, AISettingsIn, AccessHistoryItem, ConsentOut, ConsentPurpose, CycleIn, CycleOut, CycleStats,
  ExportOut, LifestyleIn, LifestyleOut, LifestyleSummary, MoodIn, MoodOut, ProfileIn, ProfileOut,
  RegisterRequest, SymptomIn, SymptomOut, TokenPair, UserOut,
} from '@/types/api';

import { api as defaultApi } from './client';

/** Every route the app calls. A contract test checks each one exists in the backend's OpenAPI document. */
export const ROUTES = {
  register: ['post', '/auth/register'], login: ['post', '/auth/login'], refresh: ['post', '/auth/refresh'],
  logout: ['post', '/auth/logout'], forgot: ['post', '/auth/forgot-password'], reset: ['post', '/auth/reset-password'],
  me: ['get', '/auth/me'],
  profileGet: ['get', '/profile'], profilePut: ['put', '/profile'],
  consentsGet: ['get', '/consents'], consentSet: ['put', '/consents/{purpose}'],
  cyclesList: ['get', '/cycles'], cycleCreate: ['post', '/cycles'], cycleUpdate: ['put', '/cycles/{item_id}'],
  cycleDelete: ['delete', '/cycles/{item_id}'], cycleStats: ['get', '/cycles/stats'],
  symptomsList: ['get', '/symptoms'], symptomCreate: ['post', '/symptoms'], symptomDelete: ['delete', '/symptoms/{item_id}'],
  lifestyleList: ['get', '/lifestyle'], lifestyleCreate: ['post', '/lifestyle'], lifestyleUpdate: ['put', '/lifestyle/{item_id}'],
  lifestyleSummary: ['get', '/lifestyle/summary'],
  moodList: ['get', '/mood'], moodCreate: ['post', '/mood'],
  aiGet: ['get', '/privacy/ai-settings'], aiPut: ['put', '/privacy/ai-settings'],
  accessHistory: ['get', '/privacy/access-history'], export: ['post', '/privacy/export'],
  deleteAccount: ['delete', '/privacy/account'],
} as const satisfies Record<string, readonly [string, string]>;

const fill = (tpl: string, params: Record<string, string>): string =>
  tpl.replace(/\{(\w+)\}/g, (_, k: string) => encodeURIComponent(params[k] ?? ''));

export type DateRange = { date_from?: string; date_to?: string; limit?: number; offset?: number };

export function createEndpoints(http: AxiosInstance = defaultApi) {
  return {
    // auth
    register: async (body: RegisterRequest) => (await http.post<UserOut>(ROUTES.register[1], body)).data,
    login: async (email: string, password: string, device?: string) =>
      (await http.post<TokenPair>(ROUTES.login[1], { email, password, device })).data,
    logout: async () => { await http.post(ROUTES.logout[1]); },
    forgotPassword: async (email: string) => { await http.post(ROUTES.forgot[1], { email }); },
    resetPassword: async (token: string, new_password: string) => { await http.post(ROUTES.reset[1], { token, new_password }); },
    me: async () => (await http.get<UserOut>(ROUTES.me[1])).data,
    // profile + consent
    getProfile: async () => (await http.get<ProfileOut>(ROUTES.profileGet[1])).data,
    putProfile: async (body: ProfileIn) => (await http.put<ProfileOut>(ROUTES.profilePut[1], body)).data,
    getConsents: async () => (await http.get<ConsentOut[]>(ROUTES.consentsGet[1])).data,
    setConsent: async (purpose: ConsentPurpose, granted: boolean) =>
      (await http.put<ConsentOut>(fill(ROUTES.consentSet[1], { purpose }), { granted })).data,
    // cycles
    listCycles: async (p: DateRange = {}) => (await http.get<CycleOut[]>(ROUTES.cyclesList[1], { params: p })).data,
    createCycle: async (body: CycleIn) => (await http.post<CycleOut>(ROUTES.cycleCreate[1], body)).data,
    updateCycle: async (id: string, body: CycleIn) => (await http.put<CycleOut>(fill(ROUTES.cycleUpdate[1], { item_id: id }), body)).data,
    deleteCycle: async (id: string) => { await http.delete(fill(ROUTES.cycleDelete[1], { item_id: id })); },
    cycleStats: async () => (await http.get<CycleStats>(ROUTES.cycleStats[1])).data,
    // symptoms
    listSymptoms: async (p: DateRange & { symptom_code?: string } = {}) => (await http.get<SymptomOut[]>(ROUTES.symptomsList[1], { params: p })).data,
    createSymptom: async (body: SymptomIn) => (await http.post<SymptomOut>(ROUTES.symptomCreate[1], body)).data,
    deleteSymptom: async (id: string) => { await http.delete(fill(ROUTES.symptomDelete[1], { item_id: id })); },
    // lifestyle
    listLifestyle: async (p: DateRange = {}) => (await http.get<LifestyleOut[]>(ROUTES.lifestyleList[1], { params: p })).data,
    createLifestyle: async (body: LifestyleIn) => (await http.post<LifestyleOut>(ROUTES.lifestyleCreate[1], body)).data,
    updateLifestyle: async (id: string, body: LifestyleIn) => (await http.put<LifestyleOut>(fill(ROUTES.lifestyleUpdate[1], { item_id: id }), body)).data,
    lifestyleSummary: async (days = 7) => (await http.get<LifestyleSummary>(ROUTES.lifestyleSummary[1], { params: { days } })).data,
    // mood
    listMood: async (p: DateRange = {}) => (await http.get<MoodOut[]>(ROUTES.moodList[1], { params: p })).data,
    createMood: async (body: MoodIn) => (await http.post<MoodOut>(ROUTES.moodCreate[1], body)).data,
    // privacy
    getAISettings: async () => (await http.get<AISettings>(ROUTES.aiGet[1])).data,
    putAISettings: async (body: AISettingsIn) => (await http.put<AISettings>(ROUTES.aiPut[1], body)).data,
    accessHistory: async (limit = 50, offset = 0) => (await http.get<AccessHistoryItem[]>(ROUTES.accessHistory[1], { params: { limit, offset } })).data,
    exportData: async () => (await http.post<ExportOut>(ROUTES.export[1])).data,
    deleteAccount: async (password: string) => { await http.delete(ROUTES.deleteAccount[1], { data: { password, confirm: 'DELETE' } }); },
  };
}

export type Endpoints = ReturnType<typeof createEndpoints>;
export const endpoints: Endpoints = createEndpoints();
