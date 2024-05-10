import pytest

from app.constants import Action, CountryCode, Entity
from app.schemas.buyable import BuyableCreateSchema, BuyableMessageSchema
from app.workers import BuyableMessageWorker, Message
from tests.msg_templator.base import entity_msg
from tests.utils import custom_uuid


@pytest.fixture
async def buyable_message_mock_worker(worker_settings, mocker):
    db_engine_mock = mocker.AsyncMock()
    worker_redis_mock = mocker.AsyncMock()
    return BuyableMessageWorker(
        Entity.BUYABLE,
        worker_settings,
        db_engine_mock,
        worker_redis_mock,
        BuyableMessageSchema,
    )


@pytest.mark.anyio
async def test_process_many_delete_messages(
    buyable_message_mock_worker: BuyableMessageWorker, mocker
):
    mock_crud = mocker.patch.object(buyable_message_mock_worker.service, "remove_many")
    db_conn_mock = mocker.AsyncMock()

    messages = [
        Message(
            identifier=custom_uuid(1), version=1, body={"id": 1}, action=Action.DELETE
        ),
        Message(
            identifier=custom_uuid(2), version=1, body={"id": 2}, action=Action.DELETE
        ),
    ]

    await buyable_message_mock_worker.process_many_delete_messages(db_conn_mock, messages)
    mock_crud.assert_called_once_with(
        db_conn_mock,
        buyable_message_mock_worker.redis,
        [
            (messages[0].identifier, messages[0].version),
            (messages[1].identifier, messages[1].version),
        ],
    )


@pytest.mark.anyio
async def test_process_many_delete_messages_exception(
    buyable_message_mock_worker: BuyableMessageWorker, mocker, caplog
):
    mock_crud = mocker.patch.object(buyable_message_mock_worker.service, "remove_many")
    db_conn_mock = mocker.AsyncMock()
    mock_crud.side_effect = Exception("Crud Error")

    messages = [
        Message(
            identifier=custom_uuid(1), version=1, body={"id": 1}, action=Action.DELETE
        )
    ]

    await buyable_message_mock_worker.process_many_delete_messages(db_conn_mock, messages)
    assert caplog.records[0].levelname == "ERROR"
    assert caplog.messages[0] == "Error in process delete buyable messages"


@pytest.mark.anyio
async def test_process_many_create_update_messages(
    buyable_message_mock_worker: BuyableMessageWorker, mocker
):
    mock_crud = mocker.patch.object(buyable_message_mock_worker.service, "upsert_many")
    db_conn_mock = mocker.AsyncMock()

    messages = [
        Message(
            identifier=custom_uuid(1),
            version=1,
            body=entity_msg(
                Entity.BUYABLE, Action.CREATE, {"offerId": custom_uuid(1), "version": 1}
            ),
            action=Action.CREATE,
        ),
        Message(
            identifier=custom_uuid(2),
            version=1,
            body=entity_msg(
                Entity.BUYABLE,
                Action.CREATE,
                {"offerId": custom_uuid(2), "version": 1, "buyable": False},
            ),
            action=Action.CREATE,
        ),
    ]

    await buyable_message_mock_worker.process_many_create_update_messages(
        db_conn_mock, messages
    )
    mock_crud.assert_called_once_with(
        db_conn_mock,
        buyable_message_mock_worker.redis,
        [
            BuyableCreateSchema(
                id=messages[0].body["offerId"],
                version=messages[0].body["version"],
                country_code=CountryCode.HU,
                buyable=True,
            ),
            BuyableCreateSchema(
                id=messages[1].body["offerId"],
                version=messages[1].body["version"],
                country_code=CountryCode.HU,
                buyable=False,
            ),
        ],
    )


@pytest.mark.anyio
async def test_process_many_create_update_messages_exception(
    buyable_message_mock_worker: BuyableMessageWorker, mocker, caplog
):
    mock_crud = mocker.patch.object(buyable_message_mock_worker.service, "upsert_many")
    db_conn_mock = mocker.AsyncMock()
    mock_crud.side_effect = Exception("Crud Error")

    messages = [
        Message(
            identifier=custom_uuid(1),
            version=1,
            body=entity_msg(
                Entity.BUYABLE, Action.CREATE, {"offerId": custom_uuid(1), "version": 1}
            ),
            action=Action.CREATE,
        )
    ]

    await buyable_message_mock_worker.process_many_create_update_messages(
        db_conn_mock, messages
    )
    assert caplog.records[0].levelname == "ERROR"
    assert caplog.messages[0] == "Error in process many create update buyable messages"
