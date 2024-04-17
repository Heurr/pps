import pytest

from app.services.base import BaseMessageService
from tests.utils import custom_uuid


@pytest.fixture
def base_message_service(mocker):
    mock_crud = mocker.AsyncMock()
    mock_entity = mocker.Mock()
    mock_create_schema = mocker.Mock()
    return BaseMessageService(mock_crud, mock_entity, mock_create_schema)


@pytest.mark.anyio
async def test_get_many_calls_crud_get_many(base_message_service, mocker):
    mock_crud = mocker.patch.object(base_message_service.crud, "get_many")
    db_conn_mock = mocker.AsyncMock()
    await base_message_service.get_many(db_conn_mock)
    mock_crud.assert_called_once_with(db_conn_mock, skip=0, limit=100)


@pytest.mark.anyio
async def test_get_many_by_ids_calls_crud_get_in(base_message_service, mocker):
    mock_crud = mocker.patch.object(base_message_service.crud, "get_in")
    db_conn_mock = mocker.AsyncMock()
    await base_message_service.get_many_by_ids(
        db_conn_mock, [custom_uuid(0), custom_uuid(1)]
    )
    mock_crud.assert_called_once_with(db_conn_mock, [custom_uuid(0), custom_uuid(1)])


@pytest.mark.anyio
async def test_upsert_calls_crud_upsert_many(base_message_service, mocker):
    mock_crud = mocker.patch.object(base_message_service.crud, "upsert_many")
    db_conn_mock = mocker.AsyncMock()
    await base_message_service.upsert_many(db_conn_mock, [])
    mock_crud.assert_called_once()


@pytest.mark.anyio
async def test_remove_calls_crud_remove_with_version_checking(
    base_message_service, mocker
):
    mock_crud = mocker.patch.object(
        base_message_service.crud, "remove_many_with_version_checking"
    )
    db_conn_mock = mocker.AsyncMock()
    await base_message_service.remove_many(db_conn_mock, [(custom_uuid(0), 1)])
    mock_crud.assert_called_once_with(db_conn_mock, [(custom_uuid(0), 1)])