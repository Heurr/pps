from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import Entity, ProductPriceType
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.schemas.shop import (
    ShopCreateSchema,
    ShopDBSchema,
)
from app.services.base import BaseEntityService
from app.utils.price_event import create_price_event_from_offer


class ShopService(BaseEntityService[ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(Entity.SHOP)

    async def generate_price_events_for_new(
        self, db_conn: AsyncConnection, new_shop: ShopCreateSchema
    ) -> list[PriceEvent]:
        if new_shop.certified:
            return await self.generate_shop_price_events(
                db_conn,
                new_shop.id,
                PriceEventAction.UPSERT,
            )
        return []

    async def generate_price_events_for_updated(
        self,
        db_conn: AsyncConnection,
        orig_db_shop: ShopDBSchema,
        new_shop: ShopCreateSchema,
    ) -> list[PriceEvent]:
        event_action: PriceEventAction | None = None

        if not orig_db_shop.certified and new_shop.certified:
            event_action = PriceEventAction.UPSERT
        if orig_db_shop.certified and not new_shop.certified:
            event_action = PriceEventAction.DELETE

        if not event_action:
            return []

        return await self.generate_shop_price_events(db_conn, new_shop.id, event_action)

    async def generate_price_events_for_delete(
        self, db_conn: AsyncConnection, orig_db_shop: ShopDBSchema
    ) -> list[PriceEvent]:
        if orig_db_shop.certified:
            return await self.generate_shop_price_events(
                db_conn,
                orig_db_shop.id,
                PriceEventAction.DELETE,
            )
        return []

    @staticmethod
    async def generate_shop_price_events(
        db_conn: AsyncConnection, shop_id: UUID, action: PriceEventAction
    ) -> list[PriceEvent]:
        return [
            create_price_event_from_offer(
                offer=offer,
                price_type=ProductPriceType.IN_STOCK_CERTIFIED,
                action=action,
            )
            for offer in await crud.shop.get_offers_in_stock_for_shops(db_conn, [shop_id])
        ]
