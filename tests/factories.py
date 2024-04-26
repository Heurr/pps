from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode, CurrencyCode
from app.schemas.offer import OfferCreateSchema, OfferDBSchema
from app.schemas.shop import ShopCreateSchema, ShopDBSchema
from app.utils import utc_now
from tests.utils import (
    random_country_code,
    random_currency_code,
    random_int,
    random_one_id,
)


async def shop_factory(  # noqa
    db_conn: AsyncConnection | None = None,
    db_schema: bool = False,
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
    if db_conn:
        return (await crud.shop.create_many(db_conn, [schema]))[0]
    elif db_schema:
        return ShopDBSchema(
            **schema.model_dump(), created_at=utc_now(), updated_at=utc_now()
        )
    else:
        return schema


async def offer_factory(
    db_conn: AsyncConnection | None = None,
    db_schema: bool = False,
    offer_id: UUID | None = None,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    shop_id: UUID | None = None,
    price: float | None = None,
    currency_code: CurrencyCode | None = None,
    version: int | None = None,
    in_stock: bool | None = None,
    availability_version: int = -1,
    buyable: bool | None = None,
    buyable_version: int = -1,
    certified_shop: bool | None = None,
) -> OfferCreateSchema | OfferDBSchema:
    schema = OfferCreateSchema(
        id=offer_id or random_one_id(),
        product_id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        shop_id=shop_id or random_one_id(),
        price=price or float(random_int()),
        currency_code=currency_code or random_currency_code(),
        version=version or random_int(),
        in_stock=in_stock,
        availability_version=availability_version,
        buyable=buyable,
        buyable_version=buyable_version,
    )
    if db_conn:
        return (await crud.offer.create_many(db_conn, [schema]))[0]
    elif db_schema:
        return OfferDBSchema(
            **schema.model_dump(),
            certified_shop=certified_shop,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
    else:
        return schema
