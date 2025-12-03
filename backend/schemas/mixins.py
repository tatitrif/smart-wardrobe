"""Миксины для Pydantic-схем с общими полями (id, временные метки, активность)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .types import IDType


class IDMixin(BaseModel):
    """Миксин: id."""

    id: IDType


class TimestampMixin(BaseModel):
    """Миксин: временные метки."""

    created_at: datetime
    updated_at: datetime


class IsActiveMixin(BaseModel):
    """Миксин: флаг активности (soft-delete)."""

    is_active: bool


class BaseReadMixin(TimestampMixin, IsActiveMixin, IDMixin):
    """Комбинированный миксин для всех схем чтения (Read-схем)."""

    model_config = ConfigDict(from_attributes=True)
