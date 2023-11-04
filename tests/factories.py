from uuid import UUID

from pendulum import Date
from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode, CurrencyCode, ProductPriceType
from app.schemas.availability import AvailabilityCreateSchema, AvailabilityDBSchema
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema
from app.schemas.offer import OfferCreateSchema, OfferDBSchema
from app.schemas.product_discount import (
    ProductDiscountCreateSchema,
    ProductDiscountDBSchema,
)
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema
from app.schemas.product_price_history import (
    ProductPriceHistoryCreateSchema,
    ProductPriceHistoryDBSchema,
)
from app.schemas.shop import ShopCreateSchema, ShopDBSchema
from tests.utils import (
    date_now,
    random_bool,
    random_country_code,
    random_currency_code,
    random_int,
    random_one_id,
    random_product_price_type,
)


async def shop_factory(  # noqa
    db_conn: AsyncConnection,
    create: bool = True,
    shop_id: UUID | None = None,
    certificated: bool | None = None,
    verified: bool | None = None,
    enabled: bool | None = None,
    paying: bool | None = None,
    version: int | None = None,
) -> ShopCreateSchema | ShopDBSchema:
    schema = ShopCreateSchema(
        id=shop_id or random_one_id(),
        version=version or random_int(),
        certificated=certificated or False,
        verified=verified or False,
        enabled=enabled or False,
        paying=paying or False,
    )
    if create:
        return await crud.shop.create(db_conn, schema)
    return schema


async def offer_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    offer_id: UUID | None = None,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    shop_id: UUID | None = None,
    amount: float | None = None,
    currency_code: CurrencyCode | None = None,
    version: int | None = None,
) -> OfferCreateSchema | OfferDBSchema:
    schema = OfferCreateSchema(
        id=offer_id or random_one_id(),
        product_id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        shop_id=shop_id or random_one_id(),
        amount=amount or float(random_int()),
        currency_code=currency_code or random_currency_code(),
        version=version or random_int(),
    )
    if create:
        return await crud.offer.create(db_conn, schema)
    return schema


async def buyable_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    buyable_id: UUID | None = None,
    buyable: bool | None = None,
    version: int | None = None,
) -> BuyableCreateSchema | BuyableDBSchema:
    schema = BuyableCreateSchema(
        id=buyable_id or random_one_id(),
        buyable=buyable or random_bool(),
        version=version or random_int(),
    )
    if create:
        return await crud.buyable.create(db_conn, schema)
    return schema


async def availability_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    availability_id: UUID | None = None,
    in_stock: bool | None = None,
    version: int | None = None,
) -> AvailabilityCreateSchema | AvailabilityDBSchema:
    schema = AvailabilityCreateSchema(
        id=availability_id or random_one_id(),
        in_stock=in_stock or random_bool(),
        version=version or random_int(),
    )
    if create:
        return await crud.availability.create(db_conn, schema)
    return schema


async def product_price_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    currency_code: CurrencyCode | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    avg_price: float | None = None,
    price_type: ProductPriceType | None = None,
    version: int | None = None,
) -> ProductPriceCreateSchema | ProductPriceDBSchema:
    schema = ProductPriceCreateSchema(
        id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        currency_code=currency_code or random_currency_code(),
        max_price=max_price or float(random_int()),
        min_price=min_price or float(random_int()),
        avg_price=avg_price or float(random_int()),
        price_type=price_type or random_product_price_type(),
        version=version or random_int(),
    )
    if create:
        return await crud.product_price.create(db_conn, schema)
    return schema


async def product_discount_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    discount: float | None = None,
    price_type: ProductPriceType | None = None,
    version: int | None = None,
) -> ProductDiscountCreateSchema | ProductDiscountDBSchema:
    schema = ProductDiscountCreateSchema(
        id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        discount=discount or float(random_int()),
        price_type=price_type or random_product_price_type(),
        version=version or random_int(),
    )
    if create:
        return await crud.product_discount.create(db_conn, schema)
    return schema


async def product_price_history_factory(
    db_conn: AsyncConnection,
    create: bool = True,
    product_id: UUID | None = None,
    country_code: CountryCode | None = None,
    currency_code: CurrencyCode | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    avg_price: float | None = None,
    price_type: ProductPriceType | None = None,
    date: Date | None = None,
    version: int | None = None,
) -> ProductPriceHistoryCreateSchema | ProductPriceHistoryDBSchema:
    schema = ProductPriceHistoryCreateSchema(
        id=product_id or random_one_id(),
        country_code=country_code or random_country_code(),
        currency_code=currency_code or random_currency_code(),
        max_price=max_price or float(random_int()),
        min_price=min_price or float(random_int()),
        avg_price=avg_price or float(random_int()),
        price_type=price_type or random_product_price_type(),
        date=date or date_now(),
        version=version or random_int(),
    )
    if create:
        return await crud.product_price_history.create(db_conn, schema)
    return schema
