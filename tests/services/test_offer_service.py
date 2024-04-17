import pytest

from tests.factories import offer_factory


@pytest.mark.anyio
async def test_upsert_many(db_conn, offer_service):
    msgs = [await offer_factory(db_conn) for i in range(3)]

    res = await offer_service.upsert_many(db_conn, msgs)

    # TODO finish tests after crud will be finished
    # assert len(res) == 3
