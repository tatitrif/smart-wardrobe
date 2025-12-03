"""Базовые классы и аннотации для моделей SQLAlchemy."""

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.annotation import Annotated

from .mixins import TableNameMixin, IDMixin, TimestampMixin, IsActiveMixin, ReprMixin

short_str = Annotated[str, "short"]
long_str = Annotated[str, "long"]
color_hex = Annotated[str, "color_hex"]


class DeclarativeBaseModel(
    AsyncAttrs,
    DeclarativeBase,
    TableNameMixin,
    IDMixin,
    TimestampMixin,
    IsActiveMixin,
    ReprMixin,
):
    """Родительский класс всех классов модели данных.

    Включает миксины для:
    - автоматического имени таблицы
    - целочисленного первичного ключа
    - временных меток
    - флага активности (soft-delete).
    """

    __abstract__ = True
    type_annotation_map = {
        short_str: String(50),
        long_str: String(255),
        color_hex: String(7),
        str: String(100),
    }
