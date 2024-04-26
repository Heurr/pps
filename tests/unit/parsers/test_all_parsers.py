from enum import Enum
from typing import TypeVar
from uuid import UUID

import orjson
import pytest

from app.constants import Action, CountryCode, Entity
from app.exceptions import ParserError
from app.parsers import (
    AvailabilityMessageParser,
    BuyableMessageParser,
    OfferMessageParser,
    ShopMessageParser,
)
from app.parsers.base import BaseParser
from app.schemas.message import MessageSchema
from tests.msg_templator.base import entity_msg
from tests.utils import custom_uuid

ParserT = TypeVar("ParserT", bound=BaseParser)

upsert_availability_msg = entity_msg(
    Entity.AVAILABILITY,
    Action.UPDATE,
    {"version": 1, "offerId": custom_uuid(1)},
    to_bytes=True,
)
upsert_buyable_msg = entity_msg(
    Entity.BUYABLE,
    Action.UPDATE,
    {"version": 1, "offerId": custom_uuid(1)},
    to_bytes=True,
)
upsert_offer_msg = entity_msg(
    Entity.OFFER, Action.UPDATE, {"version": 1, "id": custom_uuid(1)}, to_bytes=True
)
upsert_shop_msg = entity_msg(
    Entity.SHOP,
    Action.UPDATE,
    {"version": 1, "shop": {"id": custom_uuid(1)}},
    to_bytes=True,
)

delete_availability_msg = entity_msg(
    Entity.AVAILABILITY,
    Action.DELETE,
    {"version": 1, "offerId": custom_uuid(1)},
    to_bytes=True,
)
delete_buyable_msg = entity_msg(
    Entity.BUYABLE,
    Action.DELETE,
    {"version": 1, "offerId": custom_uuid(1)},
    to_bytes=True,
)
delete_offer_msg = entity_msg(
    Entity.OFFER, Action.DELETE, {"version": 1, "id": custom_uuid(1)}, to_bytes=True
)
delete_shop_msg = entity_msg(
    Entity.SHOP,
    Action.DELETE,
    {"version": 1, "shop": {"id": custom_uuid(1)}},
    to_bytes=True,
)

upsert_data = [
    (
        AvailabilityMessageParser(Entity.AVAILABILITY, throw_errors=False),
        upsert_availability_msg,
        Entity.AVAILABILITY,
        "SK",
        custom_uuid(1),
        1,
    ),
    (
        BuyableMessageParser(Entity.BUYABLE, throw_errors=False),
        upsert_buyable_msg,
        Entity.BUYABLE,
        "HU",
        custom_uuid(1),
        1,
    ),
    (
        OfferMessageParser(Entity.OFFER, throw_errors=False),
        upsert_offer_msg,
        Entity.OFFER,
        "CZ",
        custom_uuid(1),
        1,
    ),
    (
        ShopMessageParser(Entity.SHOP, throw_errors=False),
        upsert_shop_msg,
        Entity.SHOP,
        "HU",
        custom_uuid(1),
        1,
    ),
]

delete_data = [
    (
        AvailabilityMessageParser(Entity.AVAILABILITY, throw_errors=False),
        delete_availability_msg,
        Entity.AVAILABILITY,
        custom_uuid(1),
        1,
    ),
    (
        BuyableMessageParser(Entity.BUYABLE, throw_errors=False),
        delete_buyable_msg,
        Entity.BUYABLE,
        custom_uuid(1),
        1,
    ),
    (
        OfferMessageParser(Entity.OFFER, throw_errors=False),
        delete_offer_msg,
        Entity.OFFER,
        custom_uuid(1),
        1,
    ),
    (
        ShopMessageParser(Entity.SHOP, throw_errors=False),
        delete_shop_msg,
        Entity.SHOP,
        custom_uuid(1),
        1,
    ),
]


def id_fun(val):
    if isinstance(val, Enum):
        return val.value + "-"
    else:
        return ""


@pytest.mark.parametrize(
    "parser_class,msg,entity,country_code,entity_id,version", upsert_data, ids=id_fun
)
def test_parse_upsert_message(
    parser_class: ParserT,
    msg: bytes,
    # This parameter is used for the id function
    entity: Entity,
    country_code: CountryCode,
    entity_id: UUID,
    version: int,
):
    msg = orjson.loads(msg)
    assert version == parser_class.get_version(msg)
    assert country_code == parser_class.get_message_country(msg)
    assert entity_id == parser_class.get_message_id(msg)


@pytest.mark.parametrize(
    "parser_class,msg,entity,entity_id,version", delete_data, ids=id_fun
)
def test_parse_delete_message(
    parser_class: ParserT,
    msg: bytes,
    # This parameter is used for the id function
    entity: Entity,
    entity_id: UUID,
    version: int,
):
    msg = orjson.loads(msg)
    assert parser_class.get_version(msg) == version
    assert parser_class.get_message_id(msg) == entity_id


def test_parse_msg_body():
    parser = OfferMessageParser(Entity.OFFER, False)
    msg = parser.parse_message_body(upsert_offer_msg)
    assert msg == MessageSchema(
        entity=Entity.OFFER, country_code="CZ", msg=upsert_offer_msg, action=Action.UPDATE
    )


def test_parse_uuid5_throwing():
    parser = OfferMessageParser(Entity.OFFER, True)
    with pytest.raises(ParserError):
        msg = parser.parse_message_body(b'{"absolute": "gibberish"}')


def test_parse_uuid5_not_throwing():
    parser = OfferMessageParser(Entity.OFFER, False)
    msg = parser.parse_message_body(b'{"absolute": "gibberish"}')
    assert msg.country_code is None
