import logging
from datetime import datetime, timezone
import json_log_formatter
import sys

class StructuredLoggerBuilder:
    """
    Structured logger builder. For the default use, it can be called
    ```
        logger = StructuredLogBuilder(__name__).build()
        logger.info('semi-important message...'
    ```
    By default, the logger is configured to log level INFO and to stderr
    """

    def __init__(self, name):
        self._formatter = DatetimeJsonFormatter()
        self._handler = logging.StreamHandler(sys.stderr)
        self._level = logging.INFO
        self._name = name

    def level(self, level):
        """
        sete the logging level
        :param level:
        :return:
        """
        self._level = level
        return self

    def handler(self, handler):
        """
        set the handler, such as a logging.FileHandler.
        :param handler:
        :return:
        """
        self._handler = handler
        return self

    def build(self):    
        """
        Builds and returns the logger.
        :return: Configured logger instance.
        """
        # Ensure the logger does not have duplicate handlers
        logger = logging.getLogger(self._name)
        # Prevent duplicate logs by disabling propagation to the root logger
        logger.propagate = False
        if logger.hasHandlers():
            logger.handlers.clear()

        # Set up the handler and formatter
        self._handler.setFormatter(self._formatter)
        logger.addHandler(self._handler)
        logger.setLevel(self._level)

        return logger


class DatetimeJsonFormatter(json_log_formatter.JSONFormatter):
    """
    JSON log formatter that includes a timestamp
    """

    def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:
        extra["message"] = message
        extra["severity"] = record.levelname
        extra["name"] = record.name
        extra["filename"] = record.filename
        extra["funcName"] = record.funcName
        extra["lineno"] = record.lineno

        # Include a timezone-aware timestamp in UTC
        if "timestamp" not in extra:
            extra["timestamp"] = datetime.now(timezone.utc).isoformat()

        if record.exc_info:
            extra["exc_info"] = self.formatException(record.exc_info)

        return extra
