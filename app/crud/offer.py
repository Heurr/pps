import logging
from typing import Type

from sqlalchemy import Table

from app.crud.base import CRUDBase
from app.db.tables.offer import offer_table
from app.schemas.offer import OfferCreateSchema, OfferDBSchema

logger = logging.getLogger(__name__)


class CRUDOffer(CRUDBase[OfferDBSchema, OfferCreateSchema]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[OfferDBSchema],
        create_scheme: Type[OfferCreateSchema],
    ):
        super().__init__(
            table,
            db_scheme,
            create_scheme,
            ["version", "product_id", "shop_id", "price", "currency_code", "updated_at"],
        )


crud_offer = CRUDOffer(
    table=offer_table,
    db_scheme=OfferDBSchema,
    create_scheme=OfferCreateSchema,
)
