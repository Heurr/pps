from app.constants import Entity, ProductPriceType
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import EntityUpdate, PriceEvent, PriceEventAction
from app.services.simple_entity import SimpleEntityBaseService
from app.utils import utc_now


class BuyableService(SimpleEntityBaseService[OfferDBSchema, BuyableCreateSchema]):
    def __init__(self):
        super().__init__(Entity.BUYABLE)

    async def generate_price_events(
        self,
        _db_conn,
        offers: list[EntityUpdate[OfferDBSchema, BuyableCreateSchema]],
    ) -> list[PriceEvent]:
        price_events = []
        created_at = utc_now()
        for offer in offers:
            # we store buyability for existing offers only
            assert offer.old
            if (offer.new and offer.new.buyable) and not offer.old.buyable:
                price_events.append(
                    PriceEvent(
                        product_id=offer.old.product_id,
                        type=ProductPriceType.MARKETPLACE,
                        action=PriceEventAction.UPSERT,
                        price=offer.old.price,
                        country_code=offer.old.country_code,
                        currency_code=offer.old.currency_code,
                        created_at=created_at,
                    )
                )
            elif (not offer.new or not offer.new.buyable) and offer.old.buyable:
                price_events.append(
                    PriceEvent(
                        product_id=offer.old.product_id,
                        type=ProductPriceType.MARKETPLACE,
                        action=PriceEventAction.DELETE,
                        old_price=offer.old.price,
                        country_code=offer.old.country_code,
                        currency_code=offer.old.currency_code,
                        created_at=created_at,
                    )
                )

        return price_events
