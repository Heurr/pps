import pytest


@pytest.mark.anyio
async def test_upsert_many(db_conn, buyable_service):
    pass
    # msgs = [await buyable_factory(db_conn) for i in range(3)]
    #
    # res = await buyable_service.upsert_many(db_conn, msgs)

    # TODO finish tests after crud will be finished
    # assert len(res) == 3
