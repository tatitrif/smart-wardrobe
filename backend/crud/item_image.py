"""CRUD-операции для модели ItemImage (картинки предметы гардероба)."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.item import ItemImage
from schemas.item_image import ItemImageCreate, ItemImageUpdate
from schemas.types import IDType

from .base import CRUDBase


class ItemImageCRUD(CRUDBase[ItemImage, ItemImageCreate, ItemImageUpdate, IDType]):
    """CRUD-операции для модели ItemImage."""

    async def count_by_item_id(self, db: AsyncSession, item_id: IDType) -> int:
        """Подсчитывает количество изображений для предмета."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.item_id == item_id)
        )
        if hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_by_item_id(
        self, db: AsyncSession, item_id: IDType
    ) -> list[ItemImage]:
        """Получает все изображения для предмета."""
        stmt = select(self.model).where(self.model.item_id == item_id)
        if hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))
        stmt = stmt.order_by(self.model.is_primary.desc(), self.model.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def set_primary(
        self, db: AsyncSession, item_id: IDType, image_id: IDType
    ) -> bool:
        """Сделать изображение основным."""
        # Снимаем is_primary со всех изображений предмета
        await db.execute(
            update(self.model)
            .where(self.model.item_id == item_id)
            .values(is_primary=False)
        )
        # Устанавливаем для указанного
        obj = await self.get(db, image_id)
        if obj and obj.item_id == item_id:
            obj.is_primary = True
            await db.commit()
            await db.refresh(obj)
            return True
        return False


# Создаём экземпляр CRUD-класса для ItemImage
item_image_crud = ItemImageCRUD(ItemImage)
