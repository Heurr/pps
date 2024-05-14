from unittest.mock import AsyncMock

import pytest

from app.config.settings import ProductPricePublishSettings
from app.constants import Action, CountryCode, CurrencyCode, ProductPriceType
from app.schemas.base import EntityHeaders
from app.schemas.product_price import (
    ProductPricePricesRabbitSchema,
    ProductPriceRabbitSchema,
)
from app.utils.product_price_entity_client import ProductPriceEntityClient
from tests.utils import custom_uuid


@pytest.fixture
def mock_settings() -> ProductPricePublishSettings:
    return ProductPricePublishSettings()


@pytest.fixture
def mock_rabbitmq_entity_client(
    mock_settings: ProductPricePublishSettings,
) -> ProductPriceEntityClient:
    client = ProductPriceEntityClient(mock_settings)
    client.exchange = AsyncMock()
    return client


@pytest.fixture
def mock_entity():
    return [
        ProductPriceRabbitSchema(
            productId=custom_uuid(1),
            currencyCode=CurrencyCode.CZK,
            countryCode=CountryCode.CZ,
            prices=[
                ProductPricePricesRabbitSchema(
                    min=1, max=10, type=ProductPriceType.IN_STOCK
                )
            ],
            version=1,
            action=Action.CREATE,
        )
    ]


@pytest.mark.anyio
async def test_send_entity(
    mock_rabbitmq_entity_client: ProductPriceEntityClient,
    mock_settings: ProductPricePublishSettings,
    mock_entity: list[ProductPriceRabbitSchema],
):
    await mock_rabbitmq_entity_client.send_entity(mock_entity)

    assert (
        mock_rabbitmq_entity_client.exchange.publish.call_args.args[0].body.decode()
        == '[{"product_id":"00000000-0000-0000-0000-000000000001","currency_code":"CZK",'
        + '"country_code":"CZ","prices":[{"min":1.0,"max":10.0,"price_drop":null,'
        + '"type":"IN_STOCK"}],"version":1,"action":"create"}]'
    )

    headers = EntityHeaders(
        **mock_rabbitmq_entity_client.exchange.publish.call_args.args[0].headers
    )
    assert headers.model_dump(exclude={"hg_message_id"}) == {
        "user_agent": "Product Price Service Republisher",
        "content_type": "application/json",
    }

    assert (
        mock_rabbitmq_entity_client.exchange.publish.call_args.args[1]
        == mock_settings.ROUTING_KEY
    )
    mock_rabbitmq_entity_client.exchange.publish.assert_called_once()
