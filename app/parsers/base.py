import logging
from typing import cast

import orjson

from app.constants import Entity
from app.exceptions import ParserError
from app.schemas.message import InvalidMessageSchema, MessageSchema

logger = logging.getLogger(__name__)


class BaseParser:
    def __init__(self, entity: Entity, throw_errors: bool = True):
        self.throw_errors = throw_errors
        self.entity = entity

    def handle_missing_key(self, error_string: str, msg: dict):
        if self.throw_errors:
            raise ParserError(f"Failed to get message {error_string}")
        logger.debug("Failed to get message %s in message %s", error_string, msg)

    def recursive_parser(self, keys: list[str], msg_body: dict) -> str | None:
        msg_dict: dict[str, dict] = msg_body
        for key in keys:
            if key not in msg_dict:
                return self.handle_missing_key(key, msg_body)
            msg_dict = msg_dict[key]
        return cast(str, msg_dict)

    def get_message_country(self, msg_body: dict):
        return self.recursive_parser([self.entity, "legacy", "countryCode"], msg_body)

    def get_message_id(self, msg_body: dict):
        raise NotImplementedError("Not implemented")

    def get_action(self, msg_dict: dict) -> str:
        action = self.recursive_parser(["action"], msg_dict)
        return action if action else ""

    def get_version(self, msg_dict: dict):
        version = self.recursive_parser(["version"], msg_dict)
        return int(version) if version is not None else None

    def parse_message_body(self, msg: bytes) -> MessageSchema | InvalidMessageSchema:
        try:
            json_dict: dict = orjson.loads(msg)
        except orjson.JSONDecodeError:
            logger.error("Failed to parse msg, msg is not a valid JSON %s", msg)
            return InvalidMessageSchema(entity=self.entity, msg=msg)  # type: ignore

        return MessageSchema(
            entity=self.entity,
            country_code=self.get_message_country(json_dict),
            msg=msg,  # type: ignore
            action=self.get_action(json_dict),
        )
