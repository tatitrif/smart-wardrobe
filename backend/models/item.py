"""Модель sqlalchemy для Item (предметы гардероба)."""

from sqlalchemy.orm import Mapped, mapped_column
from .base import DeclarativeBaseModel, short_str, long_str, color_hex


class Item(DeclarativeBaseModel):
    """Модель предмета одежды."""

    name: Mapped[long_str]
    brand: Mapped[short_str | None]
    category: Mapped[short_str | None]
    dominant_color: Mapped[color_hex | None] = mapped_column(
        default=None, comment="HEX-код доминирующего цвета, например #FF5733"
    )
    is_favorite: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None]
