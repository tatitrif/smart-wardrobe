"""Централизованный логгер для асинхронного FastAPI-приложения."""

import contextvars
import logging
import sys
from typing import Literal

from pythonjsonlogger import json

from .config import settings

# Контекстная переменная для trace_id (для распределённого трейсинга)
trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)


def setup_logger(
    name: str = "app",
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] | None = None,
) -> logging.Logger:
    """Создаёт и настраивает именованный логгер.

    Args:
        name: Имя логгера (обычно __name__).
        level: Уровень логирования. Если не указан — определяется из настроек.

    Returns:
        Настраиваемый экземпляр логгера.
    """
    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Форматтер в зависимости от окружения
    if settings.DEBUG:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:

        class TraceJSONFormatter(json.JsonFormatter):
            def add_fields(self, log_record, record, message_dict):
                super().add_fields(log_record, record, message_dict)
                trace_id = trace_id_ctx.get()
                if trace_id:
                    log_record["trace_id"] = trace_id

        formatter = TraceJSONFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)

    return logger
