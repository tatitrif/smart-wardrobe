"""Модуль для загрузки и обработки файлов изображений.

Содержит утилиты для сохранения загруженных файлов в хранилище
(например, MinIO, S3 или локальную файловую систему) и генерации
публичных URL для доступа к ним.
"""

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from core.config import BASE_DIR, settings
from core.logger import setup_logger

logger = setup_logger(__name__)


async def handle_file_upload(
    file: UploadFile,
    dir_location: str | None = None,
    supported_types: list[str] | None = None,
    max_size: int | None = None,
) -> str:
    """Загружает файл на сервер с валидацией.

    Args:
        file: Файл для загрузки
        dir_location: Директория для сохранения (по умолчанию из настроек)
        supported_types: Разрешенные типы файлов (по умолчанию из настроек)
        max_size: Максимальный размер файла в байтах (по умолчанию из настроек)

    Returns:
        Имя загруженного файла

    Raises:
        HTTPException: При ошибках валидации или загрузки
    """
    if dir_location is None:
        dir_location = settings.UPLOAD_DIR
    if supported_types is None:
        supported_types = settings.ALLOWED_IMAGE_TYPES
    if max_size is None:
        max_size = settings.MAX_FILE_SIZE

    # Проверка типа файла
    if not file.content_type or file.content_type not in supported_types:
        logger.warning(
            f"Попытка загрузки файла с недопустимым типом: {file.content_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(supported_types)}",
        )

    # Определение расширения файла
    _, ext = os.path.splitext(file.filename or "")
    if not ext:
        # Определяем расширение по content_type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        ext = ext_map.get(file.content_type, ".jpg")

    # Создание директории, если не существует
    upload_path = Path(BASE_DIR) / dir_location
    upload_path.mkdir(parents=True, exist_ok=True)

    # Генерация уникального имени файла
    file_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_path / file_name

    # Загрузка файла с проверкой размера
    total_size = 0
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while content := await file.read(1024 * 64):  # Читаем по 64 KB
                total_size += len(content)
                if total_size > max_size:
                    # Удаляем частично загруженный файл
                    if file_path.exists():
                        file_path.unlink()
                    logger.warning(
                        f"Файл превышает максимальный размер: {total_size} > {max_size}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Файл слишком большой. Максимальный размер: {max_size / (1024 * 1024):.1f} MB",
                    )
                await out_file.write(content)

        logger.info(f"Файл успешно загружен: {file_name} ({total_size} байт)")
        return file_name

    except HTTPException:
        raise
    except OSError as e:
        logger.error(f"Ошибка при записи файла: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при сохранении файла",
        ) from e
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке файла: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке файла",
        ) from e
