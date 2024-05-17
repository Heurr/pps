import asyncio
import random
import secrets
import string
from contextlib import asynccontextmanager
from typing import Any, TypeVar
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import (
    CountryCode,
    CurrencyCode,
    PriceType,
    ProductPriceType,
)
from app.schemas.base import BaseModel
from app.schemas.offer import OfferPrice
from app.schemas.shop import ShopState
from app.utils import dump_to_json
from app.workers.base import BaseMessageWorker

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


def random_prices(how_many: int = 1) -> list[OfferPrice]:
    prices = []
    for _i in range(how_many):
        price = OfferPrice(
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


async def push_redis_messages(
    redis_conn: Redis, redis_list: str, *messages: dict
) -> None:
    values = [msg if isinstance(msg, str) else dump_to_json(msg) for msg in messages]
    await redis_conn.lpush(redis_list, *values)


async def push_messages_and_process_them_by_worker(
    worker_redis: Redis,
    worker: BaseMessageWorker,
    *msg_bodies: dict,
    wait_multiplier: float = 1.1,
):
    worker.redis_pop_timeout = 0.01
    worker.should_consume = True
    consuming_task = asyncio.create_task(worker.consume_and_process_messages())
    redis_list = f"rmq-{worker.entity.value}"

    await push_redis_messages(
        worker_redis,
        redis_list,
        *msg_bodies,
    )

    # Wait for at least one iteration of pop messages and then stop it.
    await asyncio.sleep(0.01 * wait_multiplier)
    worker.stop_consuming()
    await asyncio.wait_for(consuming_task, timeout=1)
