from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import Entity, ProductPriceType
from app.schemas.offer import (
    OfferCreateSchema,
    OfferDBSchema,
)
from app.schemas.price_event import EntityUpdate, PriceEvent, PriceEventAction
from app.services.base import BaseEntityService
from app.utils import utc_now


class OfferService(BaseEntityService[OfferDBSchema, OfferCreateSchema]):
    def __init__(self):
        super().__init__(Entity.OFFER)

    async def generate_price_events(
        self,
        _db_conn: AsyncConnection,
        offers: list[EntityUpdate[OfferDBSchema, OfferCreateSchema]],
    ) -> list[PriceEvent]:
        created_at = utc_now()
        price_events = []
        for offer in offers:
            if offer.new:
                product_id = offer.new.product_id
                price = offer.new.price
                country_code = offer.new.country_code
                currency_code = offer.new.currency_code
                action = PriceEventAction.UPSERT
            else:
                assert offer.old  # offer.new and offer.old can't be both None
                product_id = offer.old.product_id
                price = offer.old.price
                country_code = offer.old.country_code
                currency_code = offer.old.currency_code
                action = PriceEventAction.DELETE

            price_types = [ProductPriceType.ALL_OFFERS]
            if offer.old:  # on update or delete existing offer
                if offer.old.in_stock:
                    price_types.append(ProductPriceType.IN_STOCK)
                if offer.old.buyable:
                    price_types.append(ProductPriceType.MARKETPLACE)
                if offer.old.in_stock and offer.old.certified_shop:
                    price_types.append(ProductPriceType.IN_STOCK_CERTIFIED)

            price_events += [
                PriceEvent(
                    product_id,
                    price_type,
                    action,
                    price,
                    country_code,
                    currency_code,
                    created_at,
                )
                for price_type in price_types
            ]

        return price_events
