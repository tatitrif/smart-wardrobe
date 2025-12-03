"""Базовые классы и аннотации для моделей SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase

from .mixins import IDMixin, TimestampMixin, IsActiveMixin, TableNameMixin, ReprMixin


class DeclarativeBaseModel(
    IDMixin,
    TimestampMixin,
    IsActiveMixin,
    TableNameMixin,
    ReprMixin,
    DeclarativeBase,
):
    """Родительский класс всех классов модели данных.

    Включает миксины для:
    - автоматического имени таблицы
    - целочисленного первичного ключа
    - временных меток
    - флага активности (soft-delete).
    """
