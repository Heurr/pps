from app.constants import ProductPriceType
from app.schemas.offer import OfferCreateSchema, OfferDBSchema
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.utils import utc_now


def create_price_event_from_offer(
    offer: OfferDBSchema | OfferCreateSchema,
    price_type: ProductPriceType,
    action: PriceEventAction,
    old_price: float | None = None,
) -> PriceEvent:
    """
    Create price event from given original db entities, usually offer, and other parameters.

    :param offer: Usually it is passed just DB schema.
                 Only offer event generation passes create schema.
    :param price_type:
    :param action:
    :param old_price: It is used only for offer upsert to detect price changes.
    """
    return PriceEvent(
        type=price_type,
        action=action,
        old_price=old_price,
        created_at=utc_now(),
        **offer.model_dump(
            include={"product_id", "price", "country_code", "currency_code"}
        ),
    )
