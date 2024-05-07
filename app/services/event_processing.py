from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import Aggregate, ProcessResultType, ProductPriceType
from app.custom_types import ProcessResultDataType, ProductPriceDeletePk
from app.schemas.price_event import PriceChange, PriceEvent, PriceEventAction
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema
from app.utils import utc_today


class EventProcessingService:
    async def process_events_bulk(
        self,
        db_conn: AsyncConnection,
        events: list[PriceEvent],
        product_prices: dict[tuple[UUID, ProductPriceType], ProductPriceDBSchema],
    ) -> tuple[list[ProductPriceCreateSchema], list[ProductPriceDeletePk]]:
        updates: list[ProductPriceCreateSchema] = []
        deletes: list[ProductPriceDeletePk] = []

        for event in events:
            result_type, result_data = await self._process_event(
                db_conn, event, product_prices.get((event.product_id, event.type))
            )
            if result_type == ProcessResultType.UPDATED:
                updates.append(cast(ProductPriceCreateSchema, result_data))
            elif result_type == ProcessResultType.DELETED:
                deletes.append(cast(ProductPriceDeletePk, result_data))

        return updates, deletes

    async def _process_event(
        self,
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceDBSchema | None,
    ) -> tuple[
        ProcessResultType, ProductPriceCreateSchema | tuple[UUID, ProductPriceType] | None
    ]:
        if event.action == PriceEventAction.UPSERT:
            result_type, result_data = await self._process_upsert_event(
                db_conn, event, price
            )
        else:
            result_type, result_data = await self._process_delete_event(
                db_conn, event, price
            )

        if result_type in [ProcessResultType.NOT_CHANGED, ProcessResultType.DELETED]:
            return result_type, result_data  # type: ignore[return-value]

        return ProcessResultType.UPDATED, ProductPriceCreateSchema(
            day=utc_today(),
            price_type=event.type,
            updated_at=event.created_at,
            **event.model_dump(),
            **cast(PriceChange, result_data).model_dump(),
        )

    @staticmethod
    async def _process_upsert_event(
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceDBSchema | None,
    ) -> tuple[ProcessResultType, ProcessResultDataType]:
        if not price:
            return ProcessResultType.UPDATED, PriceChange(
                min_price=event.price, max_price=event.price
            )

        max_price: float | None = price.max_price
        min_price: float | None = price.min_price

        if event.old_price == price.min_price:
            min_price = await crud.offer.get_price_for_product(
                db_conn, event.product_id, event.type, Aggregate.MIN
            )
        elif event.old_price == price.max_price:
            max_price = await crud.offer.get_price_for_product(
                db_conn, event.product_id, event.type, Aggregate.MAX
            )

        if event.price < price.min_price:
            min_price = event.price
        elif event.price > price.max_price:
            max_price = event.price

        # On upsert crud can't return None on aggregate function
        assert max_price
        assert min_price

        if max_price == price.max_price and min_price == price.min_price:
            return ProcessResultType.NOT_CHANGED, None

        return ProcessResultType.UPDATED, PriceChange(
            min_price=min_price, max_price=max_price
        )

    @staticmethod
    async def _process_delete_event(
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceDBSchema | None,
    ) -> tuple[ProcessResultType, ProcessResultDataType]:
        if not price:
            return ProcessResultType.NOT_CHANGED, None

        max_price: float | None = price.max_price
        min_price: float | None = price.min_price

        if event.old_price == price.max_price:
            max_price = await crud.offer.get_price_for_product(
                db_conn, event.product_id, event.type, Aggregate.MAX
            )
        elif event.old_price == price.min_price:
            min_price = await crud.offer.get_price_for_product(
                db_conn, event.product_id, event.type, Aggregate.MIN
            )
        else:
            return ProcessResultType.NOT_CHANGED, None

        if not min_price or not max_price:
            return ProcessResultType.DELETED, ProductPriceDeletePk(
                event.product_id, event.type
            )

        return ProcessResultType.UPDATED, PriceChange(
            min_price=min_price, max_price=max_price
        )
