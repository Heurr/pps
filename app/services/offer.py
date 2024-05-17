from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import Entity, ProductPriceType
from app.schemas.offer import (
    OfferCreateSchema,
    OfferDBSchema,
)
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.services.base import BaseEntityService
from app.utils.price_event import create_price_event_from_offer


class OfferService(BaseEntityService[OfferDBSchema, OfferCreateSchema]):
    def __init__(self):
        super().__init__(Entity.OFFER)

    async def generate_price_events_for_new(
        self, db_conn: AsyncConnection, new_offer: OfferCreateSchema  # noqa ARG002
    ) -> list[PriceEvent]:
        if new_offer:
            return [
                create_price_event_from_offer(
                    offer=new_offer,
                    price_type=ProductPriceType.ALL_OFFERS,
                    action=PriceEventAction.UPSERT,
                )
            ]
        return []

    async def generate_price_events_for_updated(
        self,
        db_conn: AsyncConnection,  # noqa ARG002
        orig_db_offer: OfferDBSchema,
        new_offer: OfferCreateSchema,
    ) -> list[PriceEvent]:
        """
        It generates all UPSERT events based on offer state (in_stock, buyable, certified_shop)
        If `product_id` original offer and new offer is different it also
        generates all necessary DELETE events for original offer.
        """
        price_types = self.get_price_type_changes(orig_db_offer)

        price_events = [
            create_price_event_from_offer(
                offer=new_offer,
                price_type=price_type,
                action=PriceEventAction.UPSERT,
                old_price=orig_db_offer.price,
            )
            for price_type in price_types
        ]
        if orig_db_offer.product_id != new_offer.product_id:
            price_events.extend(
                await self.generate_price_events_for_delete(db_conn, orig_db_offer)
            )

        return price_events

    async def generate_price_events_for_delete(
        self, db_conn: AsyncConnection, orig_db_offer: OfferDBSchema  # noqa ARG002
    ) -> list[PriceEvent]:
        price_types = self.get_price_type_changes(orig_db_offer)

        return [
            create_price_event_from_offer(
                offer=orig_db_offer,
                price_type=price_type,
                action=PriceEventAction.DELETE,
            )
            for price_type in price_types
        ]

    @staticmethod
    def get_price_type_changes(offer: OfferDBSchema) -> list[ProductPriceType]:
        """
        Get which types of price event should be generated based on previous/original offer state.
        If the offer price changes it is necessary to generate price events for all active
        price types.
        """
        price_types = [ProductPriceType.ALL_OFFERS]
        if offer.in_stock:
            price_types.append(ProductPriceType.IN_STOCK)
        if offer.buyable:
            price_types.append(ProductPriceType.MARKETPLACE)
        if offer.in_stock and offer.certified_shop:
            price_types.append(ProductPriceType.IN_STOCK_CERTIFIED)

        return price_types
