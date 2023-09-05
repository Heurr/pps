from typing import Any

import sentry_sdk

from app.config.settings import base_settings


def init_sentry(server_name: str, component: str) -> None:
    if base_settings.SENTRY_DSN is None:
        return

    sentry_sdk.init(
        dsn=base_settings.SENTRY_DSN,
        environment=base_settings.APP_ENV,
        server_name=server_name,
    )

    sentry_sdk.set_tag("component", component)


def capture_exception(exc: Exception) -> None:
    if base_settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)


def capture_message(message: str) -> None:
    if base_settings.SENTRY_DSN:
        sentry_sdk.capture_message(message)


def set_sentry_context(key: str, value: dict[str, Any]) -> None:
    if base_settings.SENTRY_DSN:
        sentry_sdk.set_context(key, value)
