from unittest.mock import AsyncMock

import orjson
import pytest

from app.constants import Entity
from app.republish.headers import RepublishHeaders
from app.republish.republish_client import RabbitmqRepublishClient
from tests.utils import custom_uuid


@pytest.fixture
async def mock_rmq_publisher_client_channel(mocker):
    connection_mock = mocker.patch("app.utils.rabbitmq_adapter.connect_robust")
    mock_channel = AsyncMock()
    connection_mock.return_value.channel = mock_channel

    mock_exchange = AsyncMock()
    mock_channel.get_exchange.return_value = mock_exchange

    yield mock_channel


@pytest.fixture
async def mock_rmq_publisher_client(mock_rmq_publisher_client_channel):
    async with RabbitmqRepublishClient(Entity.BUYABLE) as rmq:
        mock_rmq_publisher_client_channel.assert_awaited_once()
        yield rmq


@pytest.mark.anyio
async def test_republish_ids(mocker, mock_rmq_publisher_client: RabbitmqRepublishClient):
    rmq_mock = mocker.patch.object(mock_rmq_publisher_client.exchange, "publish")
    republish_id = custom_uuid(1)
    await mock_rmq_publisher_client.republish_ids([republish_id])

    rmq_mock.assert_called_once()
    assert (
        orjson.dumps({"ids": [republish_id], "entity": "buyable"})
        == rmq_mock.call_args.args[0].body
    )
    headers = RepublishHeaders(**rmq_mock.call_args.args[0].headers)
    assert headers.model_dump(exclude={"hg_message_id"}, by_alias=True) == {
        "user-agent": "Product Price Service Republisher",
        "content-type": "application/json",
        "hg-republish-to": "om-buyable.v1.update.pps",
        "hg-reply-to": "op-product-price.republish-info",
    }
    assert "hg-message-id" in rmq_mock.call_args.args[0].headers
    assert rmq_mock.call_args.args[1] == "om-buyable.v1.republish"


@pytest.mark.anyio
async def test_republish_ids_throws_exec(
    mocker, mock_rmq_publisher_client: RabbitmqRepublishClient, caplog
):
    rmq_mock = mocker.patch.object(
        mock_rmq_publisher_client.exchange, "publish", side_effect=Exception("Test Error")
    )
    republish_id = custom_uuid(1)
    await mock_rmq_publisher_client.republish_ids([republish_id])

    rmq_mock.assert_called_once()
    assert caplog.messages[-1] == "Error while republishing ids, Test Error"
