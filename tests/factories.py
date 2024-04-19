from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode, CurrencyCode
from app.schemas.availability import (
    AvailabilityCreateSchema,
    AvailabilityDBSchema,
)
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema
from app.schemas.offer import (
    OfferCreateSchema,
    OfferDBSchema,
)
from app.schemas.shop import ShopCreateSchema, ShopDBSchema
from tests.utils import (
    random_bool,
    random_country_code,
    random_currency_code,
    random_int,
    random_one_id,
)


async def shop_factory(  # noqa
    db_conn: AsyncConnection,
    create: bool = True,
    shop_id: UUID | None = None,
    certified: bool | None = None,
    verified: bool | None = None,
    enabled: bool | None = None,
    paying: bool | None = None,
    version: int | None = None,
    country_code: CountryCode | None = None,
) -> ShopCreateSchema | ShopDBSchema:
    schema = ShopCreateSchema(
        id=shop_id or random_one_id(),
        country_code=country_code or random_country_code(),
        version=version or random_int(),
        certified=certified or False,
        verified=verified or False,
        enabled=enabled or False,
        paying=paying or False,
    )
    if create:
        return (await crud.shop.create_many(db_conn, [schema]))[0]
    return schema


async def offer_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    offer_id: UUID | None = None,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    shop_id: UUID | None = None,
    price: float | None = None,
    currency_code: CurrencyCode | None = None,
    version: int | None = None,
) -> OfferCreateSchema | OfferDBSchema:
    schema = OfferCreateSchema(
        id=offer_id or random_one_id(),
        product_id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        shop_id=shop_id or random_one_id(),
        price=price or float(random_int()),
        currency_code=currency_code or random_currency_code(),
        version=version or random_int(),
    )
    if create:
        return (await crud.offer.create_many(db_conn, [schema]))[0]
    return schema


async def buyable_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    buyable_id: UUID | None = None,
    buyable: bool | None = None,
    version: int | None = None,
    country_code: CountryCode | None = None,
) -> BuyableCreateSchema | BuyableDBSchema:
    schema = BuyableCreateSchema(
        id=buyable_id or random_one_id(),
        country_code=country_code or random_country_code(),
        buyable=buyable or random_bool(),
        version=version or random_int(),
    )
    if create:
        return (await crud.buyable.create_many(db_conn, [schema]))[0]
    return schema


async def availability_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    availability_id: UUID | None = None,
    in_stock: bool | None = None,
    country_code: CountryCode | None = None,
    version: int | None = None,
) -> AvailabilityCreateSchema | AvailabilityDBSchema:
    schema = AvailabilityCreateSchema(
        id=availability_id or random_one_id(),
        country_code=country_code or random_country_code(),
        in_stock=in_stock or random_bool(),
        version=version or random_int(),
    )
    if create:
        return (await crud.availability.create_many(db_conn, [schema]))[0]
    return schema
