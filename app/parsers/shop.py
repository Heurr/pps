from uuid import UUID

from app.parsers.base import BaseParser


class ShopMessageParser(BaseParser):
    def get_message_id(self, msg_body: dict):
        entity_id = self.recursive_parser([self.entity, "id"], msg_body)
        return UUID(entity_id) if entity_id else None
