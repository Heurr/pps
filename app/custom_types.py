from datetime import date
from typing import NamedTuple
from uuid import UUID

from app.constants import ProductPriceType


class OfferPk(NamedTuple):
    product_id: UUID
    offer_id: UUID


class ProductPricePk(NamedTuple):
    day: date
    product_id: UUID
    price_type: ProductPriceType
