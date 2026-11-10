import fs from 'fs';
import path from 'path';

import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

import { createEndpoints, ROUTES } from './endpoints';

// The REAL OpenAPI document exported from the running backend code (docs/api/openapi.implemented.json).
const spec = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../docs/api/openapi.implemented.json'), 'utf8')) as {
  paths: Record<string, Record<string, unknown>>;
};
const PREFIX = '/api/v1';

describe('mobile routes vs backend OpenAPI', () => {
  it.each(Object.entries(ROUTES))('%s exists on the backend', (_name, [method, p]) => {
    const op = spec.paths[PREFIX + p]?.[method];
    expect(op).toBeDefined();
  });
  it('covers every backend operation (nothing implemented but unused or undocumented)', () => {
    const backend = Object.entries(spec.paths).filter(([p]) => p.startsWith(PREFIX))
      .flatMap(([p, ops]) => Object.keys(ops).map((m) => `${m} ${p.slice(PREFIX.length)}`));
    const mobile = Object.values(ROUTES).map(([m, p]) => `${m} ${p}`);
    expect(backend.sort()).toEqual(mobile.sort());
  });
});

describe('endpoint calls', () => {
  const http = axios.create({ baseURL: 'http://x' });
  const mock = new MockAdapter(http);
  const ep = createEndpoints(http);
  afterEach(() => mock.reset());

  it('passes query params and bodies', async () => {
    mock.onGet('/cycles').reply(200, []);
    await ep.listCycles({ date_from: '2026-01-01', limit: 5 });
    expect(mock.history.get![0]!.params).toEqual({ date_from: '2026-01-01', limit: 5 });
    mock.onPost('/cycles').reply(201, {});
    await ep.createCycle({ start_date: '2026-03-01', end_date: null, flow_intensity: 3, notes: null });
    expect(JSON.parse(mock.history.post![0]!.data)).toEqual({ start_date: '2026-03-01', end_date: null, flow_intensity: 3, notes: null });
  });
  it('fills and encodes path parameters', async () => {
    mock.onPut('/cycles/a%2Fb').reply(200, {});
    await ep.updateCycle('a/b', { start_date: '2026-03-01' });
    expect(mock.history.put![0]!.url).toBe('/cycles/a%2Fb');
    mock.onPut('/consents/health_tracking').reply(200, {});
    await ep.setConsent('health_tracking', true);
    expect(JSON.parse(mock.history.put![1]!.data)).toEqual({ granted: true });
  });
  it('sends the confirmation word with account deletion', async () => {
    mock.onDelete('/privacy/account').reply(204);
    await ep.deleteAccount('pw');
    expect(JSON.parse(mock.history.delete![0]!.data)).toEqual({ password: 'pw', confirm: 'DELETE' });
  });
});
