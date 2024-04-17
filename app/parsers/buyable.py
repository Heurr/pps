from uuid import UUID

from app.parsers.base import BaseParser


class BuyableMessageParser(BaseParser):
    def get_message_country(self, msg_body: dict):
        return self.recursive_parser(["legacy", "countryCode"], msg_body)

    def get_message_id(self, msg_body: dict):
        entity_id = self.recursive_parser(["offerId"], msg_body)
        return UUID(entity_id) if entity_id else None
