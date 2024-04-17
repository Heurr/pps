from typing import Type

from sqlalchemy import Table

from app.crud.base import CRUDBase
from app.db.tables.buyable import buyable_table
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema


class CRUDBuyable(CRUDBase[BuyableDBSchema, BuyableCreateSchema]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[BuyableDBSchema],
        create_scheme: Type[BuyableCreateSchema],
    ):
        super().__init__(
            table,
            db_scheme,
            create_scheme,
            ["version", "buyable", "updated_at"],
        )


crud_buyable = CRUDBuyable(
    table=buyable_table,
    db_scheme=BuyableDBSchema,
    create_scheme=BuyableCreateSchema,
)
