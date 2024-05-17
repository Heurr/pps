from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import Entity, ProductPriceType
from app.exceptions import PriceServiceError
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.services.simple_entity import SimpleEntityBaseService
from app.utils.price_event import create_price_event_from_offer


class AvailabilityService(
    SimpleEntityBaseService[OfferDBSchema, AvailabilityCreateSchema]
):
    def __init__(self):
        super().__init__(Entity.AVAILABILITY)

    async def generate_price_events_for_new(
        self,
        db_conn: AsyncConnection,  # noqa ARG002
        new_availability: AvailabilityCreateSchema,
    ) -> list[PriceEvent]:
        if new_availability:
            raise PriceServiceError(
                "Unexpected a new availability for generate_price_events_for_new"
            )
        return []

    async def generate_price_events_for_updated(
        self,
        db_conn: AsyncConnection,  # noqa ARG002
        orig_db_offer: OfferDBSchema,
        new_availability: AvailabilityCreateSchema,
    ) -> list[PriceEvent]:
        types_actions: list[tuple[ProductPriceType, PriceEventAction]] = []

        if new_availability.in_stock and not orig_db_offer.in_stock:
            types_actions.append((ProductPriceType.IN_STOCK, PriceEventAction.UPSERT))
            if orig_db_offer.certified_shop:
                types_actions.append(
                    (ProductPriceType.IN_STOCK_CERTIFIED, PriceEventAction.UPSERT)
                )
        if not new_availability.in_stock and orig_db_offer.in_stock:
            types_actions.append((ProductPriceType.IN_STOCK, PriceEventAction.DELETE))
            if orig_db_offer.certified_shop:
                types_actions.append(
                    (ProductPriceType.IN_STOCK_CERTIFIED, PriceEventAction.DELETE)
                )

        return [
            create_price_event_from_offer(
                offer=orig_db_offer,
                price_type=price_type,
                action=price_action,
            )
            for price_type, price_action in types_actions
        ]

    async def generate_price_events_for_delete(
        self, db_conn: AsyncConnection, orig_db_offer: OfferDBSchema  # noqa ARG002
    ):
        price_types: list[ProductPriceType] = []
        if orig_db_offer.in_stock:
            price_types.append(ProductPriceType.IN_STOCK)
            if orig_db_offer.certified_shop:
                price_types.append(ProductPriceType.IN_STOCK_CERTIFIED)

        return [
            create_price_event_from_offer(
                offer=orig_db_offer,
                price_type=price_type,
                action=PriceEventAction.DELETE,
            )
            for price_type in price_types
        ]
