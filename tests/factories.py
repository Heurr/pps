from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode, CurrencyCode, ShopCertificate, StockInfo
from app.schemas.availability import (
    AvailabilityCreateSchema,
    AvailabilityDBSchema,
    AvailabilityMessageSchema,
)
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema, BuyableMessageSchema
from app.schemas.offer import OfferCreateSchema, OfferDBSchema, OfferMessageSchema, Price
from app.schemas.shop import ShopCreateSchema, ShopDBSchema, ShopMessageSchema, ShopState
from tests.utils import (
    random_bool,
    random_country_code,
    random_currency_code,
    random_int,
    random_one_id,
    random_prices,
    random_shop_certificate,
    random_shop_state,
    random_string,
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


async def availability_message_factory(
    id_: UUID | None = None,
    version: int | None = None,
    stock_info: StockInfo | None = None,
    country_code: CountryCode | None = None,
) -> AvailabilityMessageSchema:
    return AvailabilityMessageSchema(
        id=id_ or random_one_id(),
        version=version or random_int(),
        stock_info=stock_info or StockInfo.IN_STOCK,
        country_code=country_code or random_country_code(),
    )


async def buyable_message_factory(
    id_: UUID | None = None,
    version: int | None = None,
    country_code: CountryCode | None = None,
    buyable: bool | None = None,
) -> BuyableMessageSchema:
    return BuyableMessageSchema(
        id=id_ or random_one_id(),
        version=version or random_int(),
        buyable=buyable or random_bool(),
        country_code=country_code or random_country_code(),
    )


async def offer_message_factory(
    id_: UUID | None = None,
    version: int | None = None,
    country_code: CountryCode | None = None,
    local_product_id: str | None = None,
    product_id: UUID | None = None,
    shop_id: UUID | None = None,
    prices: list[Price] | None = None,
) -> OfferMessageSchema:
    return OfferMessageSchema(
        id=id_ or random_one_id(),
        version=version or random_int(),
        country_code=country_code or random_country_code(),
        local_product_id=local_product_id or random_string(),
        product_id=product_id or random_one_id(),
        shop_id=shop_id or random_one_id(),
        prices=prices or random_prices(),
    )


async def shop_message_factory(
    id_: UUID | None = None,
    version: int | None = None,
    country_code: CountryCode | None = None,
    certified: ShopCertificate | None = None,
    state: ShopState | None = None,
) -> ShopMessageSchema:
    return ShopMessageSchema(
        id=id_ or random_one_id(),
        version=version or random_int(),
        country_code=country_code or random_country_code(),
        certified=certified or random_shop_certificate(),
        state=state or random_shop_state(),
    )
