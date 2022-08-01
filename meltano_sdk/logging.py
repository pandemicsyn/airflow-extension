from __future__ import annotations

import logging
import sys

import structlog

LEVELS = {  # noqa: WPS407
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
DEFAULT_LEVEL = "info"


def parse_log_level(log_level: dict[str, int]) -> int:
    """Parse a level descriptor into an logging level.
    Args:
        log_level: level descriptor.
    Returns:
        int: actual logging level.
    """
    return LEVELS.get(log_level.lower(), LEVELS[DEFAULT_LEVEL])


def default_logging_config(level=logging.INFO, json_format=False):
    """default/demo structlog configuration.

    Args:
        level: logging level.
        json_format: if True, use JSON format, otherwise use human-readable format.
    """
    structlog.configure(
        processors=[
            # If log level is too low, abort pipeline and throw away log entry.
            structlog.stdlib.filter_by_level,
            # Add log level to event dict.
            structlog.stdlib.add_log_level,
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # If the "exc_info" key in the event dict is either true or a
            # sys.exc_info() tuple, remove "exc_info" and render the exception
            # with traceback into the "exception" key.
            structlog.processors.format_exc_info,
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            structlog.processors.ExceptionPrettyPrinter(),
            # Render the final event dict as JSON.
            structlog.processors.JSONRenderer()
            if json_format
            else structlog.dev.ConsoleRenderer(colors=False),
        ],
        # `wrapper_class` is the bound logger that you get back from
        # get_logger(). This one imitates the API of `logging.Logger`.
        wrapper_class=structlog.stdlib.BoundLogger,
        # `logger_factory` is used to create wrapped loggers that are used for
        # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
        # string) from the final processor (`JSONRenderer`) will be passed to
        # the method of the same name as that you've called on the bound logger.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Effectively freeze configuration after creating the first bound
        # logger.
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )
