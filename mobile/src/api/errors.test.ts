import { AxiosError, type AxiosResponse } from 'axios';

import { ApiError, errorMessage, toApiError } from './errors';

const httpError = (status: number, data: unknown) =>
  new AxiosError('x', 'ERR_BAD_REQUEST', undefined, undefined, { status, data } as AxiosResponse);

describe('toApiError', () => {
  it('reads the backend error envelope', () => {
    const e = toApiError(httpError(403, { error: { code: 'consent_required', message: 'Consent for health_tracking is required.', request_id: 'r1' } }));
    expect(e).toBeInstanceOf(ApiError);
    expect([e.status, e.code, e.requestId, e.isConsentRequired, e.isNetwork]).toEqual([403, 'consent_required', 'r1', true, false]);
  });
  it('falls back for responses without an envelope', () => {
    const e = toApiError(httpError(502, '<html>bad gateway</html>'));
    expect([e.code, e.message]).toEqual(['http_error', 'Request failed (502).']);
  });
  it('maps missing responses to a friendly network error', () => {
    const e = toApiError(new AxiosError('Network Error', 'ERR_NETWORK'));
    expect(e.isNetwork).toBe(true);
    expect(e.message).toMatch(/Can't reach the server/);
  });
  it('maps timeouts to a distinct message', () => expect(toApiError(new AxiosError('t', 'ECONNABORTED')).message).toMatch(/too long/));
  it('handles non-axios errors and passes ApiError through', () => {
    expect(toApiError(new Error('boom')).message).toBe('boom');
    expect(toApiError('weird').code).toBe('unknown_error');
    const e = new ApiError(400, 'x', 'y');
    expect(toApiError(e)).toBe(e);
    expect(errorMessage(e)).toBe('y');
  });
});
