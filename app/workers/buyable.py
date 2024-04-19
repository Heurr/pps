from app.schemas.buyable import BuyableCreateSchema, BuyableMessageSchema
from app.workers.base import BaseMessageWorker


class BuyableMessageWorker(BaseMessageWorker[BuyableMessageSchema]):
    def to_create_schema(self, message: BuyableMessageSchema) -> BuyableCreateSchema:
        return BuyableCreateSchema(
            country_code=message.legacy.country_code, **message.model_dump()
        )
