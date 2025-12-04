"""Маршруты API для управления распознавание."""

from pathlib import Path
from typing import Annotated

from core.config import BASE_DIR, settings
from core.db import get_db
from core.logger import setup_logger
from crud.item import item_crud
from crud.item_image import item_image_crud
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from schemas.item import ItemCreate, ItemResponse
from schemas.item_image import ItemImageCreate
from schemas.recognition import RecognizeAndCreateResponse, RecognitionResultResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .helpers.recognition import recognize_clothing_from_multiple_images
from .helpers.upload import handle_file_upload

logger = setup_logger(__name__)
router = APIRouter(prefix="/items", tags=["items, recognize"])


@router.post(
    "/recognize",
    response_model=RecognizeAndCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Распознать и создать предмет гардероба из фотографий",
)
async def recognize_and_create_item(
    images: Annotated[
        list[UploadFile], File(description="До 10 изображений одного предмета")
    ],
    db: AsyncSession = Depends(get_db),
) -> RecognizeAndCreateResponse:
    """Загружает несколько фотографий, распознает одежду и создает предмет гардероба."""
    if not settings.RECOGNITION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Распознавание одежды отключено",
        )

    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить хотя бы одно изображение",
        )

    if len(images) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимальное количество изображений: 10",
        )

    # Загружаем все  изображения
    uploaded_files: list[str] = []
    uploaded_paths: list[Path] = []

    try:
        # Шаг 1. Загрузка изображений
        for idx, image_file in enumerate(images):
            if not image_file.content_type or not image_file.content_type.startswith(
                "image/"
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Файл {idx + 1} не является изображением",
                )

            # Загружаем файл
            file_name = await handle_file_upload(image_file)
            uploaded_files.append(file_name)
            uploaded_paths.append(Path(BASE_DIR) / settings.UPLOAD_DIR / file_name)

        logger.info(f"Загружено {len(uploaded_files)} изображений для распознавания")

        # Шаг 2. Распознавание
        recognition_result = await recognize_clothing_from_multiple_images(
            uploaded_paths
        )

        # Шаг 3. Создание Item на основе распознанных данных
        item_data = ItemCreate(
            name=recognition_result.name or "Распознанный предмет",
            brand=recognition_result.brand,
            category=recognition_result.category,
            material=recognition_result.material,
            pattern=recognition_result.pattern,
            dominant_color=recognition_result.dominant_color,
            color_palette=recognition_result.color_palette,
            season=recognition_result.season,
            occasion=recognition_result.occasion,
            tags=None,  # Теги можно добавить позже вручную
            is_favorite=False,
            notes=f"Автоматически распознано (уверенность: {recognition_result.confidence:.0%})",
        )

        # Создаем запись в БД
        item = await item_crud.create(db, obj_in=item_data)

        # Шаг 4. Привязка изображений к предмету
        for idx, file_name in enumerate(uploaded_files):
            is_primary = idx == 0  # Первое изображение - основное
            # Можно определить угол по индексу или другим способом
            angle_map = {0: "front", 1: "back", 2: "label", 3: "detail"}
            angle = angle_map.get(idx)

            item_image_data = ItemImageCreate(
                item_id=item.id,
                image_url=file_name,
                is_primary=is_primary,
                angle=angle,
            )

            # Если это первое изображение, снимаем флаг с других (на случай если они уже есть)
            if is_primary:
                await db.execute(
                    update(item_image_crud.model)
                    .where(item_image_crud.model.item_id == item.id)
                    .values(is_primary=False)
                )
                await db.commit()

            await item_image_crud.create(db, obj_in=item_image_data)

        logger.info(
            f"Предмет гардероба создан на основе распознавания: {item.id} "
            f"({len(uploaded_files)} изображений)"
        )

        # Шаг 5. Ответ

        recognition_response = RecognitionResultResponse(
            category=recognition_result.category,
            name=recognition_result.name,
            brand=recognition_result.brand,
            material=recognition_result.material,
            pattern=recognition_result.pattern,
            dominant_color=recognition_result.dominant_color,
            color_palette=recognition_result.color_palette,
            season=recognition_result.season,
            occasion=recognition_result.occasion,
            confidence=recognition_result.confidence,
        )

        return RecognizeAndCreateResponse(
            item=ItemResponse.model_validate(item, from_attributes=True),
            recognition=recognition_response,
            images_count=len(uploaded_files),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при распознавании и создании предмета: {e}")
        # Удаляем загруженные файлы в случае ошибки
        for file_name in uploaded_files:
            try:
                from .helpers.upload import delete_uploaded_file

                await delete_uploaded_file(file_name)
            except Exception as cleanup_error:
                logger.warning(f"Не удалось удалить файл {file_name}: {cleanup_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при распознавании и создании предмета",
        ) from e
