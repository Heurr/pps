from app.constants import Entity, ProductPriceType
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import EntityUpdate, PriceEvent, PriceEventAction
from app.services.simple_entity import SimpleEntityBaseService
from app.utils import utc_now


class AvailabilityService(
    SimpleEntityBaseService[OfferDBSchema, AvailabilityCreateSchema]
):
    def __init__(self):
        super().__init__(Entity.AVAILABILITY)

    async def generate_price_events(
        self,
        _db_conn,
        offers: list[EntityUpdate[OfferDBSchema, AvailabilityCreateSchema]],
    ) -> list[PriceEvent]:
        price_events = []
        created_at = utc_now()
        for offer in offers:
            # we store availability for existing offers only
            assert offer.old
            types_actions: list[tuple[ProductPriceType, PriceEventAction]] = []

            if (offer.new and offer.new.in_stock) and not offer.old.in_stock:
                types_actions.append((ProductPriceType.IN_STOCK, PriceEventAction.UPSERT))
                if offer.old.certified_shop:
                    types_actions.append(
                        (ProductPriceType.IN_STOCK_CERTIFIED, PriceEventAction.UPSERT)
                    )
            elif (not offer.new or not offer.new.in_stock) and offer.old.in_stock:
                types_actions.append((ProductPriceType.IN_STOCK, PriceEventAction.DELETE))
                if offer.old.certified_shop:
                    types_actions.append(
                        (ProductPriceType.IN_STOCK_CERTIFIED, PriceEventAction.DELETE)
                    )

            for type_, action in types_actions:
                price_events.append(
                    PriceEvent(
                        product_id=offer.old.product_id,
                        type=type_,
                        action=action,
                        price=offer.old.price
                        if action == PriceEventAction.UPSERT
                        else None,
                        old_price=offer.old.price
                        if action == PriceEventAction.DELETE
                        else None,
                        country_code=offer.old.country_code,
                        currency_code=offer.old.currency_code,
                        created_at=created_at,
                    )
                )

        return price_events
