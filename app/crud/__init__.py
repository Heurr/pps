from ..constants import Entity
from .availability import crud_availability as availability
from .base import CRUDBase
from .buyable import crud_buyable as buyable
from .offer import crud_offer as offer
from .shop import crud_shop as shop

CRUD_CLASS_MAP: dict[Entity, CRUDBase] = {
    Entity.AVAILABILITY: availability,
    Entity.BUYABLE: buyable,
    Entity.OFFER: offer,
    Entity.SHOP: shop,
}


def crud_from_entity(entity: Entity) -> CRUDBase:
    return CRUD_CLASS_MAP[entity]


__all__ = ["shop", "offer", "availability", "buyable", "crud_from_entity"]
