import { ApiError } from './errors';
import { createQueryClient } from './queryClient';

describe('query retry policy', () => {
  const retry = createQueryClient().getDefaultOptions().queries!.retry as (n: number, e: unknown) => boolean;
  it('never retries client errors (400-499)', () => {
    for (const s of [400, 401, 403, 404, 409]) expect(retry(0, new ApiError(s, 'x', 'y'))).toBe(false);
  });
  it('retries network/server errors at most twice', () => {
    expect(retry(0, new ApiError(0, 'network_error', 'y'))).toBe(true);
    expect(retry(1, new ApiError(503, 'x', 'y'))).toBe(true);
    expect(retry(2, new ApiError(503, 'x', 'y'))).toBe(false);
  });
  it('never retries mutations', () => expect(createQueryClient().getDefaultOptions().mutations!.retry).toBe(false));
});
