import logging

from pydantic import ValidationError

from app.schemas.offer import OfferCreateSchema, OfferMessageSchema, OfferPrice

from ..constants import PriceType
from ..exceptions import WorkerFailedParseMsgError
from .base import BaseMessageWorker

logger = logging.getLogger(__name__)


class OfferMessageWorker(BaseMessageWorker[OfferMessageSchema]):
    def to_create_schema(self, message: OfferMessageSchema) -> OfferCreateSchema:
        price = self.parse_prices(message.prices)

        return OfferCreateSchema(
            country_code=message.legacy.country_code,
            price=price.amount,
            currency_code=price.currency_code,
            **message.model_dump(),
        )

    @staticmethod
    def parse_prices(prices: list[OfferPrice]) -> OfferPrice:
        try:
            for price in prices:
                if price.type == PriceType.REGULAR:
                    return price
        except ValidationError as err:
            raise WorkerFailedParseMsgError(
                f"Failed to parse prices field: {str(err)}"
            ) from None

        raise WorkerFailedParseMsgError(
            "Failed to get regular price. Does not exist in prices."
        )

    def is_desired_message(self, message: OfferMessageSchema) -> bool:
        if not message.product_id:
            return False
        return True
