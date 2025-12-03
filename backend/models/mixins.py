"""Миксины для моделей SQLAlchemy с поддержкой soft-delete и временных меток."""

import uuid
from datetime import datetime
from typing import Union

from sqlalchemy import DateTime, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy.sql import func

from core.config import settings

IDType = Union[int, uuid.UUID]


class IDMixin:
    """Динамический первичный ключ: int для SQLite, UUID для PostgreSQL."""

    if settings.USE_UUID:
        id: Mapped[uuid.UUID] = mapped_column(
            Uuid,
            primary_key=True,
            default=uuid.uuid4,
            index=True,
        )
    else:
        id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
            index=True,
            autoincrement=True,
        )


class TimestampMixin:
    """Автоматически управляет created_at и updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IsActiveMixin:
    """Добавляет флаг активности (для soft-delete)."""

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )


class TableNameMixin:
    """Автоматически задаёт имя таблицы."""

    @declared_attr
    def __tablename__(cls) -> str:  # noqa
        return cls.__name__.lower()


class ReprMixin:
    """Форматирует repr."""

    def __repr__(self) -> str:  # noqa
        cols = []
        for key, value in self.__dict__.items():
            if not key.startswith("_") and not callable(value):
                cols.append(f"{key}={value!r}")
                if len(cols) >= 3:
                    break
        return f"<{self.__class__.__name__} {' '.join(cols)}>"
