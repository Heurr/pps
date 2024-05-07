from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.custom_types import ProductPricePk
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema


class ProductPriceService:
    def __init__(self):
        self.crud = crud.product_price
        self.logger = getLogger(self.__class__.__name__)

    async def upsert_many(
        self,
        db_conn: AsyncConnection,
        new_objs: list[ProductPriceCreateSchema],
        db_objs: list[ProductPriceDBSchema],
    ) -> list[ProductPricePk]:
        if not new_objs:
            return []

        new_objs_map = {
            ProductPricePk(pp.day, pp.product_id, pp.price_type): pp for pp in new_objs
        }
        db_objs_map = {
            ProductPricePk(pp.day, pp.product_id, pp.price_type): pp for pp in db_objs
        }
        objs_to_upsert: list[ProductPriceCreateSchema] = []

        for new_obj_pk, new_obj in new_objs_map.items():
            db_obj = db_objs_map.get(new_obj_pk)
            if db_obj is None or db_obj.updated_at < new_obj.updated_at:
                objs_to_upsert.append(new_obj)

        return await self.crud.upsert_many(db_conn, objs_to_upsert)
