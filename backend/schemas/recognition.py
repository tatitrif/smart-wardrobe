"""Схемы для результатов распознавания одежды."""

from pydantic import BaseModel, Field

from .item import ItemResponse
from .types import HexColorStr


class RecognitionResultResponse(BaseModel):
    """Результат распознавания одежды."""

    category: str | None = Field(None, description="Категория одежды")
    name: str | None = Field(None, description="Название предмета")
    brand: str | None = Field(None, description="Бренд")
    material: str | None = Field(None, description="Материал")
    pattern: str | None = Field(None, description="Узор")
    dominant_color: HexColorStr | None = Field(None, description="Доминирующий цвет")
    color_palette: list[HexColorStr] | None = Field(None, description="Палитра цветов")
    season: list[str] | None = Field(None, description="Сезонность")
    occasion: list[str] | None = Field(None, description="Повод")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Уверенность распознавания"
    )


class RecognizeAndCreateResponse(BaseModel):
    """Ответ на запрос распознавания и создания предмета."""

    item: ItemResponse = Field(..., description="Созданный предмет гардероба")
    recognition: RecognitionResultResponse = Field(
        ..., description="Результаты распознавания"
    )
    images_count: int = Field(..., description="Количество загруженных изображений")
