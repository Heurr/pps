from typing import Type

from ..constants import Entity
from ..schemas.availability import AvailabilityMessageSchema
from ..schemas.base import MessageModel
from ..schemas.buyable import BuyableMessageSchema
from ..schemas.offer import OfferMessageSchema
from ..schemas.shop import ShopMessageSchema
from .availability import AvailabilityMessageWorker
from .base import BaseMessageWorker, Message
from .buyable import BuyableMessageWorker
from .offer import OfferMessageWorker
from .shop import ShopMessageWorker

WORKER_CLASS_MAP: dict[Entity, tuple[Type[BaseMessageWorker], Type[MessageModel]]] = {
    Entity.AVAILABILITY: (AvailabilityMessageWorker, AvailabilityMessageSchema),
    Entity.BUYABLE: (BuyableMessageWorker, BuyableMessageSchema),
    Entity.OFFER: (OfferMessageWorker, OfferMessageSchema),
    Entity.SHOP: (ShopMessageWorker, ShopMessageSchema),
}


__all__ = [
    "Message",
    "OfferMessageWorker",
    "ShopMessageWorker",
    "BuyableMessageWorker",
    "AvailabilityMessageWorker",
    "WORKER_CLASS_MAP",
]
