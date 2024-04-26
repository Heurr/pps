from app.schemas.shop import ShopCreateSchema, ShopMessageSchema
from app.workers.base import BaseMessageWorker


class ShopMessageWorker(BaseMessageWorker[ShopMessageSchema]):
    def to_create_schema(self, message: ShopMessageSchema) -> ShopCreateSchema:
        shop = message.shop

        return ShopCreateSchema(
            id=shop.id,
            version=message.version,
            country_code=shop.legacy.country_code,
            certified=shop.certificate.enabled or False,
            **shop.state.model_dump(),
        )

    def is_desired_message(self, message: ShopMessageSchema) -> bool:
        shop = message.shop
        if any(
            [
                shop.state.enabled,
                shop.state.paying,
                shop.state.verified,
                shop.certificate.enabled,
            ]
        ):
            return True
        return False
