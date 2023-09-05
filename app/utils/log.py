import logging
import sys
from datetime import datetime
from typing import Any

import orjson
from pythonjsonlogger import jsonlogger

from app.constants import LogFormatType
from app.config.log import log_setting as settings


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self, log_record: dict, record: logging.LogRecord, message_dict: dict
    ):
        """Can be used for adding another fields based on existing fields."""
        super().add_fields(log_record, record, message_dict)
        log_record["severity"] = record.levelname.upper()
        log_record["eventTime"] = (
            datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        )

    @staticmethod
    def orjson_dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
        """To ensure compatibility with orjson, so that logging is as fast as possible."""
        return orjson.dumps(obj).decode("utf-8")


class LogHandler(logging.StreamHandler):
    def handle(  # pylint: disable=useless-super-delegation
        self, record: logging.LogRecord
    ) -> bool:
        """Can be used for adding another meta information into record."""
        return super().handle(record)


def prepare_logging():
    if settings.LOG_FORMAT == LogFormatType.JSON_LOGGER:
        formatter = JsonFormatter(
            "%(created)%(funcName)%(pathname)%(lineno)%(name)%(message)",
            json_serializer=JsonFormatter.orjson_dumps,
        )

    else:
        formatter = logging.Formatter(
            "%(asctime)s:%(name)s:%(levelname)s %(message)s", "%Y%m%d %H:%M:%S"
        )

    logger = logging.getLogger()
    log_handler = LogHandler(sys.stdout)
    log_handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(log_handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # reinitialize all exist loggers
    for name in logging.root.manager.loggerDict:  # pylint: disable=no-member
        _ = logging.getLogger(name)
