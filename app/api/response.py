from typing import Any

import orjson
import pendulum
from starlette.responses import JSONResponse


class ORJsonResponse(JSONResponse):
    media_type = "application/json"

    @staticmethod
    def default(obj: Any) -> Any:
        if isinstance(obj, pendulum.DateTime):
            return obj.to_rfc3339_string()
        raise TypeError

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, default=self.default, option=orjson.OPT_INDENT_2)
