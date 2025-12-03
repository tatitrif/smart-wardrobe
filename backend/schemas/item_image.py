"""Pydantic-схемы для модели Item (предметы гардероба)."""

from pydantic import BaseModel, Field

from .common import PaginatedResponse
from .mixins import BaseReadMixin
from .types import AngleStr, IDType


class ItemImageBase(BaseModel):
    """Схема ответа при получении данных об изображении предмета."""

    item_id: IDType
    image_url: str | None = Field(None, description="URL изображения")
    is_primary: bool | None = None
    angle: AngleStr | None = Field(None, description="Угол съёмки")


class ItemImageCreate(ItemImageBase):
    """Схема создания."""


class ItemImageUpdate(ItemImageBase):
    """Схема обновления."""


class ItemImageResponse(ItemImageBase, BaseReadMixin):
    """Схема ответа картинки предмета — все поля + id, временные метки, is_active."""


ItemImageListResponse = PaginatedResponse[ItemImageResponse]
