from uuid import UUID

import pytest

from app.schemas.availability import AvailabilityMessageSchema

AVAILABILITY_RAW_MSG_IN_STOCK = """{
        "offerId": "637a3a78-7878-7878-7878-783531353632",
        "version": 123,
        "action": "update",
        "availability": {
          "legacy": {
            "platformId": "HEU",
            "countryCode": "CZ",
            "platformAvailabilityId": 1
          },
          "source": "REGULAR_FEED",
          "itemId": "999",
          "quantity": 42,
          "stockInfo": "IN_STOCK",
          "delivery": null
        }
    }"""

AVAILABILITY_RAW_MSG_DAYS = """{
        "offerId": "637a3a78-7878-7878-7878-783531353632",
        "version": 123,
        "action": "update",
        "availability": {
          "legacy": {
            "platformId": "HEU",
            "countryCode": "CZ",
            "platformAvailabilityId": 1
          },
          "source": "REGULAR_FEED",
          "itemId": "999",
          "quantity": 42,
          "stockInfo": "OUT_OF_STOCK",
          "delivery": {
            "type": "DAYS",
            "value": "3"
          }
        }
    }"""

AVAILABILITY_RAW_MSG_DATETIME = """{
        "offerId": "637a3a78-7878-7878-7878-783531353632",
        "version": 123,
        "action": "update",
        "availability": {
          "legacy": {
            "platformId": "HEU",
            "countryCode": "CZ",
            "platformAvailabilityId": 1
          },
          "source": "REGULAR_FEED",
          "itemId": "999",
          "quantity": 42,
          "stockInfo": "OUT_OF_STOCK",
          "delivery": {
            "type": "DATE-TIME",
            "value": "2022-11-20 12:00"
          }
        }
    }"""

AVAILABILITY_RAW_MSG_STRING = """{
        "offerId": "637a3a78-7878-7878-7878-783531353632",
        "version": 123,
        "action": "update",
        "availability": {
          "legacy": {
            "platformId": "HEU",
            "countryCode": "CZ",
            "platformAvailabilityId": 1
          },
          "source": "REGULAR_FEED",
          "itemId": "999",
          "quantity": 42,
          "stockInfo": "OUT_OF_STOCK",
          "delivery": {
            "type": "STRING",
            "value": "within 2 days"
          }
        }
    }"""

AVAILABILITY_RAW_MSG_NONE = """{
        "offerId": "637a3a78-7878-7878-7878-783531353632",
        "version": 123,
        "action": "update",
        "availability": {
          "legacy": {
            "platformId": "HEU",
            "countryCode": "CZ",
            "platformAvailabilityId": 1
          },
          "source": "REGULAR_FEED",
          "itemId": "999",
          "quantity": 42,
          "stockInfo": "OUT_OF_STOCK"
        }
    }"""


@pytest.mark.anyio
async def test_parse_message_body_in_stock(availability_worker):
    msg = availability_worker.parse_redis_message(AVAILABILITY_RAW_MSG_IN_STOCK)
    availability: AvailabilityMessageSchema = availability_worker.to_message_schema(msg)
    assert availability.id == UUID("637a3a78-7878-7878-7878-783531353632")
    assert availability.availability.stock_info
    assert availability.version == 123
    assert availability.availability.legacy.country_code
