from redis.asyncio import Redis

from app.core.exceptions import AppError


class LoginLimiter:
    """Fixed-window attempt counter keyed by (email, ip). Cleared on successful login."""

    def __init__(self, redis: Redis, max_attempts: int, window_seconds: int) -> None:
        self.r, self.max, self.window = redis, max_attempts, window_seconds

    @staticmethod
    def key(email: str, ip: str | None) -> str:
        return f"rl:login:{email.lower()}:{ip or '-'}"

    async def check(self, email: str, ip: str | None) -> None:
        n = await self.r.get(self.key(email, ip))
        if n is not None and int(n) >= self.max:
            raise AppError(429, "rate_limited", "Too many attempts. Try again later.")

    async def failure(self, email: str, ip: str | None) -> None:
        k = self.key(email, ip)
        n = await self.r.incr(k)
        if n == 1:
            await self.r.expire(k, self.window)

    async def reset(self, email: str, ip: str | None) -> None:
        await self.r.delete(self.key(email, ip))
