"""Миксины для Pydantic-схем с общими полями (id, временные метки, активность)."""

from datetime import datetime

from core.config import settings
from pydantic import BaseModel, ConfigDict


class IDMixin(BaseModel):
    """Миксин: id."""

    if settings.USE_UUID:
        id: str
    else:
        id: int


class TimestampMixin(BaseModel):
    """Миксин: временные метки."""

    created_at: datetime
    updated_at: datetime


class IsActiveMixin(BaseModel):
    """Миксин: флаг активности (для soft-delete)."""

    is_active: bool = True


class BaseReadMixin(IDMixin, TimestampMixin, IsActiveMixin):
    """Комбинированный миксин для всех схем чтения (Read-схем)."""

    model_config = ConfigDict(from_attributes=True)
