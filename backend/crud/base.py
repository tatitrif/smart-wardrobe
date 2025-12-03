"""Базовый асинхронный CRUD-миксин для SQLAlchemy моделей."""

from typing import Generic, TypeVar
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Универсальный асинхронный CRUD-класс для работы с SQLAlchemy моделями."""

    def __init__(self, model: type[ModelType]):
        """Инициализирует CRUD-объект для заданной модели.

        Args:
            model: Класс SQLAlchemy-модели.
        """
        self.model = model

    async def get(self, db: AsyncSession, id: int | str) -> ModelType | None:
        """Получить запись по ID (только активные, если есть is_active)."""
        stmt = select(self.model).where(self.model.id == id)
        # Поддержка soft-delete через миксин IsActiveMixin
        if hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> tuple[list[ModelType], int]:
        """Получить список записей + общее количество (с поддержкой пагинации)."""
        # Подсчёт общего числа
        count_stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "is_active"):
            count_stmt = count_stmt.where(self.model.is_active.is_(True))

        total = await db.scalar(count_stmt)

        # Запрос с пагинацией
        stmt = select(self.model).offset(skip).limit(limit)
        if hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))
        if hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())

        result = await db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Создать новую запись."""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """Обновить существующую запись."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int | str) -> bool:
        """Удалить запись (soft-delete, если поддерживается)."""
        obj = await self.get(db, id)
        if not obj:
            return False

        if hasattr(obj, "is_active"):
            # Soft-delete
            obj.is_active = False
        else:
            # Hard-delete
            await db.delete(obj)

        await db.commit()
        return True
