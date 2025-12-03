"""Маршруты API для управления item."""

from core.db import get_db
from crud.item import item_crud
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.types import IDType
from schemas.item import ItemCreate, ItemResponse, ItemUpdate, ItemListResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый предмет гардероба",
)
async def create_item(
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Создаёт новый предмет гардероба."""
    item = await item_crud.create(db, obj_in=item_data)
    return ItemResponse.model_validate(item, from_attributes=True)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Получить предмет гардероба по ID",
)
async def read_item(
    item_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Возвращает предмет гардероба по его ID."""
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return ItemResponse.model_validate(item, from_attributes=True)


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
    response_model=ItemResponse,
    summary="Частично обновить предмет гардероба",
)
async def update_item(
    item_id: IDType,
    item_data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Обновляет по ID те поля, которые нужно изменить."""
    db_item = await item_crud.get(db, id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    item = await item_crud.update(db, db_obj=db_item, obj_in=item_data)
    return ItemResponse.model_validate(item, from_attributes=True)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить предмет гардероба",
)
async def delete_item(
    item_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет предмет гардероба (soft-delete)."""
    success = await item_crud.remove(db, id=item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
