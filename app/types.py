from datetime import date
from typing import NamedTuple
from uuid import UUID

from app.constants import ProductPriceType


class ProductPricePk(NamedTuple):
    day: date
    product_id: UUID
    price_type: ProductPriceType
