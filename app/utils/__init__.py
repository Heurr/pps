from typing import Any
from uuid import UUID

import orjson
from pendulum import DateTime, now
from pydantic import BaseModel

from app.constants import COUNTRY_PLATFORM_MAP, CountryCode, PlatformCode


def utc_now() -> DateTime:
    return now()


def version_now() -> int:
    return DateTime.utcnow().int_timestamp


def get_platform_for_country(country_code: CountryCode) -> PlatformCode:
    return COUNTRY_PLATFORM_MAP[country_code]


def dump_to_json(obj: Any) -> str:
    def default(obj_: Any):
        if isinstance(obj_, (UUID, DateTime)):
            return str(obj_)
        if isinstance(obj_, BaseModel):
            return obj_.dict()
        raise TypeError

    return orjson.dumps(obj, default=default).decode("utf-8")
