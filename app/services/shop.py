from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import Entity, ProductPriceType
from app.schemas.price_event import EntityUpdate, PriceEvent, PriceEventAction
from app.schemas.shop import (
    ShopCreateSchema,
    ShopDBSchema,
)
from app.services.base import BaseEntityService
from app.utils import utc_now


class ShopService(BaseEntityService[ShopDBSchema, ShopCreateSchema]):
    def __init__(self):
        super().__init__(Entity.SHOP)

    async def generate_price_events(
        self,
        db_conn: AsyncConnection,
        shops: list[EntityUpdate[ShopDBSchema, ShopCreateSchema]],
    ) -> list[PriceEvent]:
        upsert_event_shop_ids = []
        delete_event_shop_ids = []
        for shop in shops:
            if (shop.new and shop.new.certified) and (
                not shop.old or not shop.old.certified
            ):
                upsert_event_shop_ids.append(shop.new.id)
            elif (not shop.new or not shop.new.certified) and (
                shop.old and shop.old.certified
            ):
                delete_event_shop_ids.append(shop.old.id)

        created_at = utc_now()
        price_events = [
            PriceEvent(
                product_id=offer.product_id,
                type=ProductPriceType.IN_STOCK_CERTIFIED,
                action=PriceEventAction.UPSERT,
                price=offer.price,
                country_code=offer.country_code,
                currency_code=offer.currency_code,
                created_at=created_at,
            )
            for offer in await crud.shop.get_offers_in_stock_for_shops(
                db_conn, upsert_event_shop_ids
            )
        ] + [
            PriceEvent(
                product_id=offer.product_id,
                type=ProductPriceType.IN_STOCK_CERTIFIED,
                action=PriceEventAction.DELETE,
                old_price=offer.price,
                country_code=offer.country_code,
                currency_code=offer.currency_code,
                created_at=created_at,
            )
            for offer in await crud.shop.get_offers_in_stock_for_shops(
                db_conn, delete_event_shop_ids
            )
        ]

        return price_events
