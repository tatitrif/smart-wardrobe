"""Маршруты API для управления ItemImage."""

from typing import Annotated

from core.db import get_db
from core.logger import setup_logger
from crud.item import item_crud
from crud.item_image import item_image_crud
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from schemas.item_image import (
    ItemImageCreate,
    ItemImageResponse,
)
from schemas.types import IDType, AngleStr
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .helpers.upload import handle_file_upload

logger = setup_logger(__name__)
router = APIRouter(prefix="/item_images", tags=["item_images"])


@router.post(
    "/{item_id}",
    response_model=ItemImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую привязку картинка - предмет гардероба",
)
async def create_item_image(
    item_id: IDType,
    image_file: Annotated[UploadFile, File(media_type="image/*")],
    is_primary: bool | None = Form(
        None, description="Является ли изображение основным"
    ),
    angle: AngleStr | None = Form(None, description="Угол съёмки"),
    db: AsyncSession = Depends(get_db),
) -> ItemImageResponse:
    """Создает новую привязку изображения к предмету гардероба."""
    # Проверка существования предмета перед загрузкой файла
    item = await item_crud.get(db, id=item_id)
    if not item:
        logger.warning(
            f"Попытка добавить изображение к несуществующему предмету: {item_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # Проверка типа файла
    if not image_file.content_type or not image_file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
        )

    # Загрузка файла
    try:
        file_url = await handle_file_upload(image_file)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла для item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        ) from e

    # Определяем, является ли это первым изображением
    images_count = await item_image_crud.count_by_item_id(db, item_id)
    if is_primary is None:
        # Автоматически устанавливаем is_primary=True для первого изображения
        is_primary = images_count == 0

    # Подготовка данных для создания
    item_image_data = ItemImageCreate(
        item_id=item_id,
        image_url=file_url,
        is_primary=is_primary,
        angle=angle,
    )

    # Если устанавливаем is_primary=True, снимаем флаг с других изображений
    if is_primary:
        await db.execute(
            update(item_image_crud.model)
            .where(item_image_crud.model.item_id == item_id)
            .values(is_primary=False)
        )

    # Создание записи в БД
    try:
        item_image = await item_image_crud.create(db, obj_in=item_image_data)
        logger.info(
            f"Изображение успешно добавлено к предмету {item_id}: {item_image.id}"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании записи изображения для item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create image record",
        ) from e

    return ItemImageResponse.model_validate(item_image, from_attributes=True)


@router.get(
    "/item/{item_id}",
    response_model=list[ItemImageResponse],
    summary="Получить все изображения предмета",
)
async def get_item_images(
    item_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> list[ItemImageResponse]:
    """Возвращает все изображения для указанного предмета гардероба."""
    # Проверка существования предмета
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    item_images = await item_image_crud.get_by_item_id(db, item_id)
    return [
        ItemImageResponse.model_validate(img, from_attributes=True)
        for img in item_images
    ]


@router.get(
    "/{item_image_id}",
    response_model=ItemImageResponse,
    summary="Получить изображение по ID",
)
async def read_item_image(
    item_image_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> ItemImageResponse:
    """Возвращает изображение по его ID."""
    item_image = await item_image_crud.get(db, id=item_image_id)
    if not item_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ItemImage not found",
        )
    return ItemImageResponse.model_validate(item_image, from_attributes=True)
