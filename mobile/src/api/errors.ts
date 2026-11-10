import { isAxiosError } from 'axios';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
  get isNetwork(): boolean { return this.code === 'network_error'; }
  get isConsentRequired(): boolean { return this.code === 'consent_required'; }
}

type Envelope = { error?: { code?: string; message?: string; request_id?: string } };

/** Normalises anything thrown by axios into an ApiError using the backend's uniform error envelope. */
export function toApiError(e: unknown): ApiError {
  if (e instanceof ApiError) return e;
  if (isAxiosError(e)) {
    if (!e.response) {
      const timedOut = e.code === 'ECONNABORTED';
      return new ApiError(0, 'network_error', timedOut ? 'The server took too long to respond.' : "Can't reach the server. Check your connection and try again.");
    }
    const env = (e.response.data as Envelope | undefined)?.error;
    return new ApiError(e.response.status, env?.code ?? 'http_error', env?.message ?? `Request failed (${e.response.status}).`, env?.request_id);
  }
  return new ApiError(-1, 'unknown_error', e instanceof Error ? e.message : 'Something went wrong.');
}

export const errorMessage = (e: unknown): string => toApiError(e).message;
