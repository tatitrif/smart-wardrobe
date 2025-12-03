"""Pydantic-схемы для модели Item (предметы гардероба)."""

from pydantic import BaseModel, Field

from .common import PaginatedResponse
from .mixins import BaseReadMixin


class ItemBase(BaseModel):
    """Базовая схема для входных данных."""

    name: str = Field(..., min_length=1, max_length=255)
    brand: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=50)
    dominant_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_favorite: bool = False
    notes: str | None = Field(None, max_length=1000)


class ItemCreate(ItemBase):
    """Схема создания."""


class ItemUpdate(ItemBase):
    """Схема обновления."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_favorite: bool | None = None


class ItemRead(ItemBase, BaseReadMixin):
    """Схема ответа — все поля + id, временные метки, is_active."""

    pass


ItemListResponse = PaginatedResponse[ItemRead]
