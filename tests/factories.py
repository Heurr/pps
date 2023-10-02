from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode
from app.schemas.product import ProductCreateSchema, ProductDBSchema

from .utils import (
    random_country_code,
    random_int,
    random_one_id,
    random_string,
)


async def product_create_schema_factory(
    db_conn: AsyncConnection,
    product_id: UUID | None = None,
    local_product_id: str | None = None,
    country: CountryCode | None = None,
    name: str | None = None,
    version: int | None = None,
) -> ProductCreateSchema:
    return ProductCreateSchema(
        id=product_id or random_one_id(),
        local_product_id=local_product_id or random_string(8),
        name=name or random_string(),
        country=country or random_country_code(),
        version=version or random_int(),
    )


async def product_factory(
    db_conn: AsyncConnection,
    product_id: UUID | None = None,
    local_product_id: str | None = None,
    country: CountryCode | None = None,
    name: str | None = None,
    version: int | None = None,
) -> ProductDBSchema:
    product_in = await product_create_schema_factory(**dict(locals().items()))
    return await crud.product.create(db_conn, product_in)
