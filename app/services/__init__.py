from typing import Type

from ..constants import Entity
from .availability import AvailabilityService
from .base import BaseEntityService
from .buyable import BuyableService
from .offer import OfferService
from .shop import ShopService

SERVICE_CLASS_MAP: dict[Entity, Type[BaseEntityService]] = {
    Entity.AVAILABILITY: AvailabilityService,
    Entity.BUYABLE: BuyableService,
    Entity.OFFER: OfferService,
    Entity.SHOP: ShopService,
}


def service_from_entity(entity: Entity) -> BaseEntityService:
    service_class: Type[BaseEntityService] = SERVICE_CLASS_MAP[entity]
    return service_class()  # type: ignore[call-arg]


__all__ = [
    "service_from_entity",
    "OfferService",
    "ShopService",
    "BuyableService",
    "AvailabilityService",
]
