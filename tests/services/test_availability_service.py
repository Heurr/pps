import pytest


@pytest.mark.anyio
async def test_upsert_many(db_conn, availability_service):
    pass
    # msgs = [await availability_factory(db_conn) for i in range(3)]
    #
    # res = await availability_service.upsert_many(db_conn, msgs)

    # TODO finish tests after crud will be finished
    # assert len(res) == 3
