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

from .helpers.upload import handle_file_upload, delete_uploaded_file

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
        await db.commit()  # Коммитим изменения перед созданием новой записи

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
    "/item/{item_id}/primary",
    response_model=ItemImageResponse | None,
    summary="Получить основное изображение предмета",
)
async def get_primary_image(
    item_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> ItemImageResponse | None:
    """Возвращает основное изображение для указанного предмета гардероба."""
    # Проверка существования предмета
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    item_images = await item_image_crud.get_by_item_id(db, item_id)
    primary_image = next((img for img in item_images if img.is_primary), None)

    if primary_image:
        return ItemImageResponse.model_validate(primary_image, from_attributes=True)
    return None


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


@router.patch(
    "/{item_image_id}",
    response_model=ItemImageResponse,
    summary="Обновить изображение",
)
async def update_item_image(
    item_image_id: IDType,
    is_primary: bool | None = Form(
        None, description="Является ли изображение основным"
    ),
    angle: AngleStr | None = Form(None, description="Угол съёмки"),
    db: AsyncSession = Depends(get_db),
) -> ItemImageResponse:
    """Обновляет изображение по ID."""
    from schemas.item_image import ItemImageUpdate

    db_item_image = await item_image_crud.get(db, id=item_image_id)
    if not db_item_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ItemImage not found",
        )

    # Если устанавливаем is_primary=True, снимаем флаг с других изображений
    if is_primary is True:
        await db.execute(
            update(item_image_crud.model)
            .where(
                item_image_crud.model.item_id == db_item_image.item_id,
                item_image_crud.model.id != item_image_id,
            )
            .values(is_primary=False)
        )
        await db.commit()

    # Подготовка данных для обновления
    update_data = ItemImageUpdate(
        item_id=db_item_image.item_id,
        image_url=db_item_image.image_url,
        is_primary=is_primary if is_primary is not None else db_item_image.is_primary,
        angle=angle if angle is not None else db_item_image.angle,
    )

    item_image = await item_image_crud.update(
        db, db_obj=db_item_image, obj_in=update_data
    )
    logger.info(f"Изображение обновлено: {item_image_id}")
    return ItemImageResponse.model_validate(item_image, from_attributes=True)


@router.delete(
    "/{item_image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить изображение",
)
async def delete_item_image(
    item_image_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет изображение (soft-delete) и связанный файл."""
    item_image = await item_image_crud.get(db, id=item_image_id)
    if not item_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ItemImage not found",
        )

    # Удаляем файл с диска
    if item_image.image_url:
        try:
            await delete_uploaded_file(item_image.image_url)
        except Exception as e:
            logger.warning(f"Не удалось удалить файл {item_image.image_url}: {e}")

    # Удаляем запись из БД (soft-delete)
    success = await item_image_crud.remove(db, id=item_image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ItemImage not found",
        )

    logger.info(f"Изображение удалено: {item_image_id}")


@router.patch(
    "/{item_image_id}/set-primary",
    response_model=ItemImageResponse,
    summary="Установить изображение как основное",
)
async def set_primary_image(
    item_image_id: IDType,
    db: AsyncSession = Depends(get_db),
) -> ItemImageResponse:
    """Устанавливает изображение как основное для предмета."""
    item_image = await item_image_crud.get(db, id=item_image_id)
    if not item_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ItemImage not found",
        )

    success = await item_image_crud.set_primary(
        db, item_id=item_image.item_id, image_id=item_image_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set primary image",
        )

    # Обновляем объект из БД
    updated_image = await item_image_crud.get(db, id=item_image_id)
    logger.info(f"Изображение {item_image_id} установлено как основное")
    return ItemImageResponse.model_validate(updated_image, from_attributes=True)
