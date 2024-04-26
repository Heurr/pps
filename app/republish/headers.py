from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class RepublishHeaders(BaseModel):
    user_agent: str = Field(alias="user-agent")
    content_type: str = Field(alias="content-type")
    hg_republish_to: str = Field(alias="hg-republish-to")
    hg_reply_to: str = Field(alias="hg-reply-to")
    hg_message_id: str = Field(
        alias="hg-message-id", default_factory=lambda: str(uuid4())
    )

    model_config = ConfigDict(populate_by_name=True)
