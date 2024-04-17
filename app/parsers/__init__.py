from typing import Type

from ..constants import Entity
from .availability import AvailabilityMessageParser
from .base import BaseParser
from .buyable import BuyableMessageParser
from .offer import OfferMessageParser
from .shop import ShopMessageParser

PARSER_CLASS_MAP: dict[Entity, Type[BaseParser]] = {
    Entity.AVAILABILITY: AvailabilityMessageParser,
    Entity.BUYABLE: BuyableMessageParser,
    Entity.OFFER: OfferMessageParser,
    Entity.SHOP: ShopMessageParser,
}


def parser_from_entity(entity: Entity, throw_errors: bool) -> BaseParser:
    parser_class: Type[BaseParser] = PARSER_CLASS_MAP[entity]
    return parser_class(entity, throw_errors)


__all__ = [
    "AvailabilityMessageParser",
    "BuyableMessageParser",
    "OfferMessageParser",
    "ShopMessageParser",
    "BaseParser",
    "parser_from_entity",
]
