"""Outbound email. Only a console backend exists (development). SMTP/SES delivery is NOT implemented yet;
in production the backend must be 'disabled' and password-reset emails are not sent."""
import logging

from app.core.config import get_settings

log = logging.getLogger("app.email")


async def send_password_reset(email: str, token: str) -> None:
    s = get_settings()
    if s.email_backend == "console" and s.app_env != "production":
        log.warning("DEV EMAIL to=%s subject='Reset your password' reset_token=%s", email, token)
    else:
        log.info("password reset email suppressed (email backend: %s)", s.email_backend)
