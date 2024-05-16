import logging
from typing import cast

from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import Aggregate, ProcessResultType
from app.custom_types import BasePricePk, ProductPriceDeletePk
from app.schemas.price_event import PriceChange, PriceEvent, PriceEventAction
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema
from app.utils import utc_today

ProcessResultDataType = PriceChange | ProductPriceDeletePk | None


class EventProcessingService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_events_bulk(
        self,
        db_conn: AsyncConnection,
        events: list[PriceEvent],
        product_prices: dict[BasePricePk, ProductPriceDBSchema],
    ) -> tuple[list[ProductPriceCreateSchema], list[ProductPriceDeletePk]]:
        """
        Processing for upserts is handled sequentially, to ensure correct data
        First a snapshot of product prices are created then events change the state
        of the snapshot and at the end the snapshot is returned to be upserted
        """
        events.sort(key=lambda e: e.created_at)
        product_prices_snapshot = {
            pk: ProductPriceCreateSchema(**product_price.model_dump())
            for pk, product_price in product_prices.items()
        }

        deletes: list[ProductPriceDeletePk] = []

        for event in events:
            result_type, result_data = await self._process_event(
                db_conn,
                event,
                product_prices_snapshot.get(BasePricePk(event.product_id, event.type)),
            )

            if result_type in (ProcessResultType.CREATED, ProcessResultType.UPDATED):
                changed_product_price = cast(ProductPriceCreateSchema, result_data)
                product_prices_snapshot[
                    BasePricePk(
                        changed_product_price.product_id, changed_product_price.price_type
                    )
                ] = changed_product_price
            elif result_type == ProcessResultType.DELETED:
                deletes.append(cast(ProductPriceDeletePk, result_data))

        return list(product_prices_snapshot.values()), deletes

    async def _process_event(
        self,
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceCreateSchema | None,
    ) -> tuple[ProcessResultType, ProductPriceCreateSchema | ProductPriceDeletePk | None]:
        if event.action == PriceEventAction.UPSERT:
            result_type, result_data = await self._process_upsert_event(
                db_conn, event, price
            )
        else:
            result_type, result_data = await self._process_delete_event(
                db_conn, event, price
            )

        if result_type == ProcessResultType.CREATED:
            return result_type, ProductPriceCreateSchema(
                day=utc_today(),
                price_type=event.type,
                updated_at=event.created_at,
                **event.model_dump(),
                **cast(PriceChange, result_data).model_dump(),
            )
        elif result_type == ProcessResultType.UPDATED:
            return result_type, ProductPriceCreateSchema(
                updated_at=event.created_at,
                day=utc_today(),
                **price.model_dump(  # type: ignore[union-attr]
                    exclude={"min_price", "max_price", "updated_at", "day"}
                ),
                **cast(PriceChange, result_data).model_dump(),
            )

        return result_type, result_data  # type: ignore[return-value]

    async def _process_upsert_event(
        self,
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceCreateSchema | None,
    ) -> tuple[ProcessResultType, ProcessResultDataType]:
        assert event.price  # UPSERT event has always price set
        if not price:
            return ProcessResultType.CREATED, PriceChange(
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

        if min_price is None or max_price is None:
            extra = {
                "event": event,
                "price": price,
                "min_price": min_price,
                "max_price": max_price,
            }
            self.logger.info("%s", extra)
            self.logger.error(
                "Invalid None value for min max price in process_upsert_event",
                extra=extra,
            )
            return ProcessResultType.INVALID, None

        if max_price == price.max_price and min_price == price.min_price:
            return ProcessResultType.NOT_CHANGED, None

        return ProcessResultType.UPDATED, PriceChange(
            min_price=min_price, max_price=max_price
        )

    @staticmethod
    async def _process_delete_event(
        db_conn: AsyncConnection,
        event: PriceEvent,
        price: ProductPriceCreateSchema | None,
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
