import datetime as dt
from typing import Any
from uuid import UUID

import orjson
from pydantic import BaseModel

from app.constants import COUNTRY_PLATFORM_MAP, CountryCode, PlatformCode


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def version_now() -> int:
    return int(dt.datetime.now(dt.timezone.utc).timestamp())


def get_platform_for_country(country_code: CountryCode) -> PlatformCode:
    return COUNTRY_PLATFORM_MAP[country_code]


def dump_to_json(obj: Any) -> str:
    def default(obj_: Any):
        if isinstance(obj_, (UUID, dt.datetime)):
            return str(obj_)
        if isinstance(obj_, BaseModel):
            return obj_.model_dump()
        raise TypeError

    return orjson.dumps(obj, default=default).decode("utf-8")
