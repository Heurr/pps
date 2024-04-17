import random
import secrets
import string
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import (
    CountryCode,
    CurrencyCode,
    PriceType,
    ProductPriceType,
    ShopCertificate,
)
from app.schemas.base import BaseModel
from app.schemas.offer import Price
from app.schemas.shop import ShopState

DBSchemaTypeT = TypeVar("DBSchemaTypeT", bound=BaseModel)
CreateSchemaTypeT = TypeVar("CreateSchemaTypeT", bound=BaseModel)


def random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_int(a: int = 1, b: int = 1000) -> int:
    return secrets.choice(range(a, b))


def random_float(a: float = 0.0, b: float = 100.0) -> float:
    return round(random.uniform(a, b), 2)


def custom_uuid(index: int) -> UUID:
    return UUID(int=index)


def random_bool() -> bool:
    return bool(random.getrandbits(1))


def random_cost(a: int = 1, b: int = 100) -> float:
    return random_int(a * 100, b * 100) / 100.0


def random_country_code(ignore: set[CountryCode] = None) -> CountryCode:
    if ignore is None:
        ignore = set()
    generate_from = list(ignore ^ set(CountryCode))
    return CountryCode(secrets.choice(generate_from))


def random_currency_code() -> CurrencyCode:
    return secrets.choice(list(CurrencyCode))


def random_product_price_type() -> ProductPriceType:
    return secrets.choice(list(ProductPriceType))


def random_shop_certificate() -> ShopCertificate:
    return secrets.choice(list(ShopCertificate))


def random_price_type() -> PriceType:
    return secrets.choice(list(PriceType))


def random_shop_state() -> ShopState:
    return ShopState(
        verified=random_bool(),
        paying=random_bool(),
        enabled=random_bool(),
        deletable=random_bool(),
    )


def random_one_id() -> UUID:
    return uuid4()


def random_prices(how_many: int = 1) -> list[Price]:
    prices = []
    for _i in range(how_many):
        price = Price(
            type=random_price_type(),
            amount=random_int(),
            currency_code=random_currency_code(),
            vat=random_float(),
        )
        prices.append(price)
    return prices


def override_obj_get_db_conn(db_conn: AsyncConnection, obj: Any) -> Any:
    @asynccontextmanager
    async def get_db_conn():
        yield db_conn

    obj.get_db_conn = get_db_conn
    return obj


def compare_obj_params(first, second, to_compare: list[str]):
    for param in to_compare:
        first_param = getattr(first, param)
        second_param = getattr(second, param)
        assert getattr(first, param) == getattr(
            second, param
        ), f"{param} doesn't equal {first_param} == {second_param}"


def compare(
    first: CreateSchemaTypeT | DBSchemaTypeT,
    second: DBSchemaTypeT,
    ignore_keys: list | None = None,
):
    """
    Compare two objects using the first objects parameters
    """
    keys = list(vars(first).keys())
    if ignore_keys:
        [keys.remove(ignore_key) for ignore_key in ignore_keys]
    compare_obj_params(first, second, keys)


def get_rmq_msgs(subdir: str):
    files = [str(f) for f in Path(Path(__file__).parent / subdir / "data").iterdir()]
    files_data = {}
    for file in files:
        key = file.split("/").pop().replace(".json", "")
        with open(file) as _f:
            files_data[key] = _f.read()
    return files_data
