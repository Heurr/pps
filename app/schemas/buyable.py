from app.schemas.base import BaseDBSchema, EntityModel


class BuyableMessageSchema(EntityModel):
    buyable: bool


class BuyableCreateSchema(EntityModel):
    buyable: bool = False


class BuyableUpdateSchema(EntityModel):
    buyable: bool | None = None


class BuyableDBSchema(BuyableCreateSchema, BaseDBSchema):
    pass
