"""Pydantic-схемы для модели Item (предметы гардероба)."""

from pydantic import BaseModel, Field

from .common import PaginatedResponse
from .mixins import BaseReadMixin
from .types import HexColorStr


class ItemBase(BaseModel):
    """Базовая схема для входных данных."""

    name: str = Field(..., min_length=1, max_length=255)
    brand: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=50)
    material: str | None = Field(
        None, max_length=50, description="Материал (хлопок, шерсть)"
    )
    pattern: str | None = Field(
        None, max_length=50, description="Тип узора: solid, stripe,"
    )
    dominant_color: HexColorStr | None = Field(None, description="HEX-цвет")
    color_palette: list[HexColorStr] | None = Field(
        None, description="Список HEX-цветов"
    )
    season: list[str] | None = Field(
        None, description="Сезонность: spring, summer, autumn, winter"
    )
    occasion: list[str] | None = Field(
        None, description="Повод: ['casual', 'work', 'party', 'sport']"
    )
    tags: list[str] | None = Field(
        None, description="Пользовательские теги: ['любимое', 'новое']"
    )
    is_favorite: bool = False
    notes: str | None = Field(None, max_length=1000)


class ItemCreate(ItemBase):
    """Схема создания."""


class ItemUpdate(ItemBase):
    """Схема обновления."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_favorite: bool | None = None
    # Остальные поля могут быть None — partial update


class ItemResponse(ItemBase, BaseReadMixin):
    """Схема ответа предмета — все поля + id, временные метки, is_active."""


ItemListResponse = PaginatedResponse[ItemResponse]
