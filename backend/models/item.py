"""Модель sqlalchemy для Item (предметы гардероба)."""


from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import DeclarativeBaseModel


class Item(DeclarativeBaseModel):
    """Модель предмета гардероба."""

    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(50))
    material: Mapped[str | None] = mapped_column(
        String(50), comment="Материал (хлопок, шерсть и т.д.)"
    )
    pattern: Mapped[str | None] = mapped_column(
        String(50), comment="Тип узора: solid, stripe, check и т.д."
    )
    dominant_color: Mapped[str | None] = mapped_column(
        String(7), default=None, comment="HEX-код доминирующего цвета, например #FF5733"
    )
    color_palette: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Список HEX-кодов основных цветов"
    )
    season: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Сезонность: ['spring', 'summer', 'autumn', 'winter']"
    )
    occasion: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Повод: ['casual', 'work', 'party', 'sport']"
    )
    tags: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Пользовательские теги: ['любимое', 'новое']"
    )
    is_favorite: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(String(1000))


