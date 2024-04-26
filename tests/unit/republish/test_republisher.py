from unittest.mock import AsyncMock

import orjson
import pytest

from app.constants import Entity
from app.republish.headers import RepublishHeaders
from app.republish.republish_client import RabbitmqRepublishClient
from tests.utils import custom_uuid


@pytest.fixture
async def mock_rmq_publisher_client(mocker):
    connection_mock = mocker.patch("app.utils.rabbitmq_adapter.connect_robust")
    mock_channel = AsyncMock()
    connection_mock.return_value.channel = mock_channel

    mock_exchange = AsyncMock()
    mock_channel.get_exchange.return_value = mock_exchange

    async with RabbitmqRepublishClient(Entity.BUYABLE) as rmq:
        mock_channel.assert_awaited_once()
        yield rmq


@pytest.mark.anyio
async def test_republish_ids(mocker, mock_rmq_publisher_client: RabbitmqRepublishClient):
    rmq_mock = mocker.patch.object(mock_rmq_publisher_client.exchange, "publish")
    republish_id = custom_uuid(1)
    await mock_rmq_publisher_client.republish_ids([republish_id])

    rmq_mock.assert_called_once()
    assert orjson.dumps({"ids": [republish_id]}) == rmq_mock.call_args.args[0].body
    headers = RepublishHeaders(**rmq_mock.call_args.args[0].headers)
    assert headers.model_dump(exclude={"hg_message_id"}) == {
        "user_agent": "Product Price Service Republisher",
        "content_type": "application/json",
        "hg_republish_to": "om-buyable.v1.republish",
        "hg_reply_to": "op-product-price-service.republish-info",
    }
    assert "hg_message_id" in rmq_mock.call_args.args[0].headers
    assert rmq_mock.call_args.args[1] == "om-buyable.v1.update.pps"


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
