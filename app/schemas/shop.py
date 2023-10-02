from app.constants import ShopCertificate
from app.schemas.base import BaseMessageModel, BaseModel


class ShopState(BaseModel):
    verified: bool | None
    paying: bool | None
    enabled: bool | None
    deletable: bool | None


class ShopMessageSchema(BaseMessageModel):
    certificate: ShopCertificate
    state: ShopState
