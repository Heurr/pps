from app.constants import ShopCertificate
from app.schemas.base import BaseDBSchema, BaseModel, EntityModel


class ShopState(BaseModel):
    verified: bool | None
    paying: bool | None
    enabled: bool | None
    deletable: bool | None


class ShopMessageSchema(EntityModel):
    certified: ShopCertificate
    state: ShopState


class ShopCreateSchema(EntityModel):
    certified: bool = False
    verified: bool = False
    paying: bool = False
    enabled: bool = False


class ShopUpdateSchema(EntityModel):
    certified: bool | None = None
    verified: bool | None = None
    paying: bool | None = None
    enabled: bool | None = None


class ShopDBSchema(ShopCreateSchema, BaseDBSchema):
    pass
