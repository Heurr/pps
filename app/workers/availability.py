from app.constants import StockInfo
from app.schemas.availability import AvailabilityCreateSchema, AvailabilityMessageSchema
from app.workers.base import BaseMessageWorker


class AvailabilityMessageWorker(BaseMessageWorker[AvailabilityMessageSchema]):
    def to_create_schema(
        self, message: AvailabilityMessageSchema
    ) -> AvailabilityCreateSchema:
        return AvailabilityCreateSchema(
            country_code=message.availability.legacy.country_code,
            in_stock=message.availability.stock_info == StockInfo.IN_STOCK,
            **message.model_dump(),
        )
