import pytest

from app import crud
from app.constants import Action, Entity
from tests.msg_templator.base import entity_msg
from tests.utils import (
    push_messages_and_process_them_by_worker,
    random_one_id,
)


@pytest.mark.anyio
async def test_process_workers_together(
    db_conn, worker_redis, offer_worker, availability_worker
):
    offer_id = random_one_id()
    product_id = random_one_id()

    offer_msgs = [
        entity_msg(
            Entity.OFFER,
            Action.CREATE,
            {
                "id": str(offer_id),
                "productId": str(product_id),
                "version": 1,
            },
        )
    ]
    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )

    availability_msgs = [
        entity_msg(
            Entity.AVAILABILITY,
            Action.CREATE,
            {
                "offerId": str(offer_id),
                "version": 2,
            },
        ),
    ]
    await push_messages_and_process_them_by_worker(
        worker_redis, availability_worker, *availability_msgs
    )

    offer_msgs = [
        entity_msg(
            Entity.OFFER,
            Action.CREATE,
            {
                "id": str(offer_id),
                "productId": str(product_id),
                "prices": [
                    {
                        "type": "regular",
                        "amount": "123.45",
                        "currencyCode": "CZK",
                        "vat": "21.0",
                    }
                ],
                "version": 3,
            },
        )
    ]
    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )

    offer = await crud.offer.get(db_conn, offer_id)
    assert offer.version == 3
    assert offer.price == 123.45
    assert offer.in_stock is True
    assert offer.availability_version == 2
