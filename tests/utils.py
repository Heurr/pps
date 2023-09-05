import secrets
import string
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import CountryCode, CurrencyCode


def random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_int(a: int = 1, b: int = 1000) -> int:
    return secrets.choice(range(a, b))


def random_cost(a: int = 1, b: int = 100) -> float:
    return random_int(a * 100, b * 100) / 100.0


def random_country_code() -> CountryCode:
    return secrets.choice(list(CountryCode))


def random_currency_code() -> CurrencyCode:
    return secrets.choice(list(CurrencyCode))


def random_one_id() -> UUID:
    return uuid4()


def override_obj_get_db_conn(db_conn: AsyncConnection, obj: Any) -> Any:
    @asynccontextmanager
    async def get_db_conn():
        yield db_conn

    obj.get_db_conn = get_db_conn
    return obj
