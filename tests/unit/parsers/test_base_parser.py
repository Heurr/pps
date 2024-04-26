import json

import pytest
from pytest import param

from app.constants import Action, Entity
from app.exceptions import ParserError
from app.parsers.offer import OfferMessageParser
from tests.msg_templator.base import entity_msg

not_throwing_data = [
    param(["legacy", "countryCode"], "CZ", False, id="all_values"),
    param(["countryCode"], None, False, id="missing_key"),
]


@pytest.fixture
def parsed_msg():
    return json.loads(entity_msg(Entity.OFFER, Action.CREATE, to_bytes=True))


def test_error_handler(caplog):
    parser = OfferMessageParser(Entity.OFFER, throw_errors=False)

    assert parser.handle_missing_key("missing key", {}) is None


def test_error_handler_throwing():
    parser = OfferMessageParser(Entity.OFFER, throw_errors=True)
    with pytest.raises(ParserError):
        parser.handle_missing_key("test", {})


@pytest.mark.parametrize("values,result,throw_errors", not_throwing_data)
def test_recursive_parser(
    parsed_msg, values: list[str], result: str | None, throw_errors: bool, caplog
):
    parser = OfferMessageParser(Entity.OFFER, throw_errors)
    country = parser.recursive_parser(values, parsed_msg)
    assert country == result


def test_recursive_parser_throw_error(parsed_msg):
    parser = OfferMessageParser(Entity.OFFER, True)
    with pytest.raises(ParserError):
        parser.recursive_parser(["countryCode"], parsed_msg)


def test_parser_not_throwing():
    parser = OfferMessageParser(Entity.OFFER, False)
    msg = parser.parse_message_body(b'{"absolute": "gibberish"}')
    assert msg.entity == Entity.OFFER
    assert msg.action == ""
    assert msg.country_code is None
    assert msg.msg == '{"absolute": "gibberish"}'
