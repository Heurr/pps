from typing import TypeVar

import pytest

from app.constants import Entity
from app.exceptions import ParserError
from app.parsers import (
    AvailabilityMessageParser,
    BuyableMessageParser,
    OfferMessageParser,
    ShopMessageParser,
)
from app.parsers.base import BaseParser
from app.schemas.message import MessageSchema
from tests.utils import get_rmq_msgs

ParserT = TypeVar("ParserT", bound=BaseParser)
messages = get_rmq_msgs("parsers")

derived_parsers_data = [
    (
        AvailabilityMessageParser(Entity.AVAILABILITY, throw_errors=False),
        messages["availability"],
        Entity.AVAILABILITY,
        MessageSchema(
            country_code="SK",
            action="update",
            entity=Entity.AVAILABILITY,
            msg=messages["availability"],
        ),
    ),
    (
        BuyableMessageParser(Entity.BUYABLE, throw_errors=False),
        messages["buyable"],
        Entity.BUYABLE,
        MessageSchema(
            country_code="HU",
            action="update",
            entity=Entity.BUYABLE,
            msg=messages["buyable"],
        ),
    ),
    (
        OfferMessageParser(Entity.OFFER, throw_errors=False),
        messages["offer"],
        Entity.OFFER,
        MessageSchema(
            country_code="CZ",
            action="update",
            entity=Entity.OFFER,
            msg=messages["offer"],
        ),
    ),
    (
        ShopMessageParser(Entity.SHOP, throw_errors=False),
        messages["shop"],
        Entity.SHOP,
        MessageSchema(
            country_code="HU",
            action="update",
            entity=Entity.SHOP,
            msg=messages["shop"],
        ),
    ),
]


def id_fun(val):
    if isinstance(val, str) and val[0] != "{":
        return val + "-"
    else:
        return ""


@pytest.mark.parametrize(
    "parser_class,msg,entity,msg_schema", derived_parsers_data, ids=id_fun
)
def test_parse_message_body(
    parser_class: ParserT,
    msg: bytes,
    # This parameter is used for the id function
    entity: Entity,
    msg_schema: MessageSchema,
):
    parsed_msg = parser_class.parse_message_body(msg)
    assert parsed_msg == msg_schema


def test_parse_uuid5_throwing():
    parser = OfferMessageParser(Entity.OFFER, True)
    with pytest.raises(ParserError):
        msg = parser.parse_message_body(b'{"absolute": "gibberish"}')


def test_parse_uuid5_not_throwing():
    parser = OfferMessageParser(Entity.OFFER, False)
    msg = parser.parse_message_body(b'{"absolute": "gibberish"}')
    assert msg.country_code is None
