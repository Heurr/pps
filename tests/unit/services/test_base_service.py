import pytest

from app.services.base import BaseEntityService
from tests.utils import custom_uuid


@pytest.fixture
def base_message_service(mocker):
    crud_from_entity_mock = mocker.patch("app.services.base.crud_from_entity")
    crud_from_entity_mock.return_value = mocker.AsyncMock()
    mock_entity = mocker.Mock()
    return BaseEntityService(mock_entity)


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
