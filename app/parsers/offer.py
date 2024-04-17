from uuid import UUID

from app.parsers.base import BaseParser


class OfferMessageParser(BaseParser):
    def get_message_country(self, msg_body: dict):
        return self.recursive_parser(["legacy", "countryCode"], msg_body)

    def get_message_id(self, msg_body: dict):
        entity_id = self.recursive_parser(["id"], msg_body)
        return UUID(entity_id) if entity_id else None
