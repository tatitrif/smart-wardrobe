"""Миксины для Pydantic-схем с общими полями (id, временные метки, активность)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IDMixin(BaseModel):
    """Миксин: id."""

    id: UUID


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
