from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import Entity, ProductPriceType
from app.exceptions import PriceServiceError
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.services.simple_entity import SimpleEntityBaseService
from app.utils.price_event import create_price_event_from_offer


class BuyableService(SimpleEntityBaseService[OfferDBSchema, BuyableCreateSchema]):
    def __init__(self):
        super().__init__(Entity.BUYABLE)

    async def generate_price_events_for_new(
        self,
        db_conn: AsyncConnection,  # noqa ARG002
        new_buyable: BuyableCreateSchema,
    ) -> list[PriceEvent]:
        if new_buyable:
            raise PriceServiceError(
                "Unexpected a new buyable for generate_price_events_for_new"
            )
        return []

    async def generate_price_events_for_updated(
        self,
        db_conn: AsyncConnection,  # noqa ARG002
        orig_db_offer: OfferDBSchema,
        new_buyable: BuyableCreateSchema,
    ) -> list[PriceEvent]:
        event_action: PriceEventAction | None = None

        if new_buyable.buyable and not orig_db_offer.buyable:
            event_action = PriceEventAction.UPSERT
        if not new_buyable.buyable and orig_db_offer.buyable:
            event_action = PriceEventAction.DELETE

        if not event_action:
            return []

        return [
            create_price_event_from_offer(
                offer=orig_db_offer,
                price_type=ProductPriceType.MARKETPLACE,
                action=event_action,
            )
        ]

    async def generate_price_events_for_delete(
        self, db_conn: AsyncConnection, orig_db_offer: OfferDBSchema  # noqa ARG002
    ):
        if orig_db_offer.buyable:
            return [
                create_price_event_from_offer(
                    offer=orig_db_offer,
                    price_type=ProductPriceType.MARKETPLACE,
                    action=PriceEventAction.DELETE,
                )
            ]
        return []
