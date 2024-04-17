from app.schemas.base import BaseDBSchema, EntityModel


class BuyableMessageSchema(EntityModel):
    buyable: bool


class BuyableCreateSchema(EntityModel):
    buyable: bool = False


class BuyableDBSchema(BuyableCreateSchema, BaseDBSchema):
    pass
