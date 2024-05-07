from datetime import date
from typing import NamedTuple
from uuid import UUID

from app.constants import ProductPriceType
from app.schemas.price_event import PriceChange


class OfferPk(NamedTuple):
    product_id: UUID
    offer_id: UUID


class ProductPricePk(NamedTuple):
    day: date
    product_id: UUID
    price_type: ProductPriceType


class ProductPriceDeletePk(NamedTuple):
    product_id: UUID
    price_type: ProductPriceType


ProcessResultDataType = PriceChange | ProductPriceDeletePk | None
