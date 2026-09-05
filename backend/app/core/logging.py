import sys
import logging
import structlog
from structlog.types import EventDict, Processor
from app.core.config import get_settings


SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "openai_api_key",
    "anthropic_api_key",
    "secret_key",
    "password",
    "token",
    "cookie",
}

LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def add_service_name(logger: structlog.BoundLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "lenny-growth-assistant"
    return event_dict


def drop_color_message_key(logger: structlog.BoundLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


def mask_sensitive_data(logger: structlog.BoundLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Mask credentials and sensitive headers from structured logs."""
    for key in list(event_dict.keys()):
        lower_key = key.lower()
        if any(sensitive in lower_key for sensitive in SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def setup_logging() -> None:
    settings = get_settings()
    level_num = LOG_LEVEL_MAP.get(settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        add_service_name,
        drop_color_message_key,
        mask_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if sys.stderr.isatty():
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "") -> structlog.BoundLogger:
    return structlog.get_logger(name)