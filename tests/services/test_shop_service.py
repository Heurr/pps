import pytest

from tests.factories import shop_factory


@pytest.mark.anyio
async def test_upsert_many(db_conn, shop_service):
    msgs = [await shop_factory(db_conn) for i in range(3)]

    res = await shop_service.upsert_many(db_conn, msgs)

    # TODO finish tests after crud will be finished
    # assert len(res) == 3
