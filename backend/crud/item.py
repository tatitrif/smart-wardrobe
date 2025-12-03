"""CRUD-операции для модели Item (предметы гардероба)."""

from .base import CRUDBase
from models.item import Item
from schemas.item import ItemCreate, ItemUpdate
from schemas.types import IDType

# Создаём экземпляр CRUD-класса для Item
item_crud = CRUDBase[Item, ItemCreate, ItemUpdate, IDType](Item)
