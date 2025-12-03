"""Общие Pydantic-схемы, используемые во всём проекте."""

from typing import TypeVar, Generic

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Стандартизированный ответ с пагинацией для списковых эндпоинтов.

    Attributes:
        items: Список элементов текущей страницы
        total: Общее количество элементов
        page: Номер текущей страницы
        size: Количество элементов на странице
        pages: Общее количество страниц
    """

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
