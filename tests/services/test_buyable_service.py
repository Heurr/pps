import pytest

from tests.factories import buyable_message_factory


@pytest.mark.anyio
async def test_upsert_many(db_conn, buyable_service):
    msgs = [await buyable_message_factory() for i in range(3)]

    res = await buyable_service.upsert_many(db_conn, msgs)

    # TODO finish tests after crud will be finished
    # assert len(res) == 3
