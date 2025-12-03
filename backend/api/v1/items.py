"""Маршруты API для управления item."""

from core.db import get_db
from crud.item import item_crud
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.item import ItemCreate, ItemRead, ItemUpdate, ItemListResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "/",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый предмет гардероба",
)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> ItemRead:
    """Создаёт новый предмет гардероба."""
    return await item_crud.create(db, obj_in=item_in)


@router.get(
    "/{item_id}",
    response_model=ItemRead,
    summary="Получить предмет гардероба по ID",
)
async def read_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> ItemRead:
    """Возвращает предмет гардероба по его ID."""
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.get(
    "/",
    response_model=ItemListResponse,
    summary="Получить список предметов гардероба",
)
async def read_items(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Количество на странице"),
    db: AsyncSession = Depends(get_db),
) -> ItemListResponse:
    """Возвращает пагинированный список активных предметов гардероба."""
    skip = (page - 1) * size
    items, total = await item_crud.get_multi(db, skip=skip, limit=size)
    pages = (total + size - 1) // size  # округление вверх

    return ItemListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/{item_id}",
    response_model=ItemRead,
    summary="Частично обновить предмет гардероба",
)
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> ItemRead:
    """Обновляет по ID те поля, которые нужно изменить."""
    db_item = await item_crud.get(db, id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return await item_crud.update(db, db_obj=db_item, obj_in=item_in)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить предмет гардероба",
)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет предмет гардероба (soft-delete)."""
    success = await item_crud.remove(db, id=item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
