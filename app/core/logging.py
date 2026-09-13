import logging
import logging.config
import os
from contextvars import ContextVar
from uuid import uuid4

REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get()
        return True


class SensitiveDataFilter(logging.Filter):
    _sensitive_names = ("authorization", "api_key", "password", "token", "secret")

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for name in self._sensitive_names:
            message = message.replace(name, f"{name[:1]}***")
        record.msg = message
        record.args = ()
        return True


def setup_logging() -> None:
    """Configure console, application, and error log handlers."""
    from app.core.config import settings

    os.makedirs(settings.log_dir, exist_ok=True)
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {"()": "app.core.logging.RequestContextFilter"},
            "sensitive_data": {"()": "app.core.logging.SensitiveDataFilter"},
        },
        "formatters": {
            "standard": {
                "format": ("%(asctime)s | %(levelname)-8s | %(name)s | "
                            "%(filename)s:%(lineno)d | request_id=%(request_id)s | %(message)s"),
                "datefmt": "%Y-%m-%d %H:%M:%S%z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "filters": ["request_context", "sensitive_data"],
                "level": settings.log_level,
            },
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.log_file,
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "encoding": "utf-8",
                "formatter": "standard",
                "filters": ["request_context", "sensitive_data"],
                "level": settings.log_level,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(settings.log_dir, "error.log"),
                "maxBytes": settings.log_max_bytes,
                "backupCount": settings.log_backup_count,
                "encoding": "utf-8",
                "formatter": "standard",
                "filters": ["request_context", "sensitive_data"],
                "level": "ERROR",
            },
        },
        "root": {
            "handlers": ["console", "app_file", "error_file"],
            "level": settings.log_level,
        },
    }
    logging.config.dictConfig(logging_config)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def configure_logging() -> None:
    """Backward-compatible alias for application startup."""
    setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Return the configured logger for a module or component."""
    return logging.getLogger(name)


def new_request_id() -> str:
    return uuid4().hex[:12]


def set_request_id(request_id: str) -> object:
    return REQUEST_ID.set(request_id)


def reset_request_id(token: object) -> None:
    REQUEST_ID.reset(token)  # type: ignore[arg-type]
