from app.constants import ShopCertificate
from app.schemas.base import BaseDBSchema, BaseIdModel, BaseMessageModel, BaseModel


class ShopState(BaseModel):
    verified: bool | None
    paying: bool | None
    enabled: bool | None
    deletable: bool | None


class ShopMessageSchema(BaseMessageModel):
    certificate: ShopCertificate
    state: ShopState


class ShopBaseSchema(BaseIdModel):
    certificated: bool = False
    verified: bool = False
    paying: bool = False
    enabled: bool = False
    version: int


class ShopUpdateSchema(BaseIdModel):
    certificated: bool | None = None
    verified: bool | None = None
    paying: bool | None = None
    enabled: bool | None = None
    version: int | None = None


class ShopCreateSchema(ShopBaseSchema):
    pass


class ShopDBSchema(ShopBaseSchema, BaseDBSchema):
    pass
