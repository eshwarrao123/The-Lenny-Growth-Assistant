import sys
import structlog
from structlog.types import EventDict, Processor


def add_service_name(logger: structlog.BoundLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "lenny-growth-assistant"
    return event_dict


def drop_color_message_key(logger: structlog.BoundLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging() -> None:
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        add_service_name,
        drop_color_message_key,
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
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "") -> structlog.BoundLogger:
    return structlog.get_logger(name)