"""Модель sqlalchemy для Item (предметы гардероба)."""

import uuid
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    images: Mapped[list["ItemImage"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class ItemImage(DeclarativeBaseModel):
    """Модель изображений предмета гардероба."""

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("item.id"))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(default=False)
    angle: Mapped[str | None] = mapped_column(String(20))

    item: Mapped["Item"] = relationship(back_populates="images")
