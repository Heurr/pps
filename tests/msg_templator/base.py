from copy import deepcopy
from typing import Any

import orjson

from app.constants import Action, Entity
from tests.msg_templator.availability import (
    AVAILABILITY_DELETE_MSG,
    AVAILABILITY_UPSERT_MSG,
)
from tests.msg_templator.buyable import BUYABLE_DELETE_MSG, BUYABLE_UPSERT_MSG
from tests.msg_templator.offer import OFFER_DELETE_MSG, OFFER_UPSERT_MSG
from tests.msg_templator.shop import SHOP_DELETE_MSG, SHOP_UPSERT_MSG

ENTITY_UPSERT_MSG_MAP: dict[Entity, dict[str, Any]] = {
    Entity.AVAILABILITY: AVAILABILITY_UPSERT_MSG,
    Entity.BUYABLE: BUYABLE_UPSERT_MSG,
    Entity.OFFER: OFFER_UPSERT_MSG,
    Entity.SHOP: SHOP_UPSERT_MSG,
}

ENTITY_DELETE_MSG_MAP: dict[Entity, dict[str, Any]] = {
    Entity.AVAILABILITY: AVAILABILITY_DELETE_MSG,
    Entity.BUYABLE: BUYABLE_DELETE_MSG,
    Entity.OFFER: OFFER_DELETE_MSG,
    Entity.SHOP: SHOP_DELETE_MSG,
}


def _replace_with_new_value(value_key: str, new_value: Any, msg_template: dict) -> None:
    """
    Replace a value inside a dict with a new value according to a specified key
    """
    for key in msg_template:
        if key == value_key:
            msg_template[key] = new_value
            return


def _replace_with_new_data(new_data: dict, msg_template: dict) -> None:
    """
    Iterate ove newr data recursively and if a key is found in booth source and template
    data, replace the key with the provided value inside the template data

    Templating lists is not nested, that means if there is a dict inside a
    list you need to provide the whole list of dicts
    """
    for key, value in new_data.items():
        if isinstance(value, dict):
            _replace_with_new_data(value, msg_template[key])
        else:
            _replace_with_new_value(key, value, msg_template)


def entity_msg(
    entity: Entity,
    action: Action,
    new_data: dict[str, Any] | None = None,
    to_bytes: bool = False,
) -> bytes | dict:
    match action:
        case Action.CREATE | Action.UPDATE:
            msg_entity_map = ENTITY_UPSERT_MSG_MAP
        case Action.DELETE:
            msg_entity_map = ENTITY_DELETE_MSG_MAP
        case _:
            raise Exception("Unknown action")
    template = deepcopy(msg_entity_map[entity])
    if new_data:
        new_data["action"] = action.value
    else:
        new_data = {"action": action.value}
    _replace_with_new_data(new_data, template)
    return orjson.dumps(template) if to_bytes else template
