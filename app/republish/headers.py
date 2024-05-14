from pydantic import Field

from app.schemas.base import BaseRMQHeaders


class RepublishHeaders(BaseRMQHeaders):
    hg_republish_to: str = Field(alias="hg-republish-to")
    hg_reply_to: str = Field(alias="hg-reply-to")
