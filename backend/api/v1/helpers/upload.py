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

# Magic bytes для проверки реального формата файла
IMAGE_MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",  # JPEG
    b"\x89\x50\x4e\x47": "image/png",  # PNG
    b"RIFF": "image/webp",  # WebP (нужна дополнительная проверка)
}


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

    # Проверка типа файла по content_type
    if not file.content_type or file.content_type not in supported_types:
        logger.warning(
            f"Попытка загрузки файла с недопустимым типом: {file.content_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(supported_types)}",
        )

    # Проверка реального формата файла через magic bytes (опционально, для безопасности)
    # Читаем первые байты файла для проверки
    file_content_start = b""
    try:
        chunk = await file.read(12)
        file_content_start = chunk
        # Возвращаемся в начало файла (если поддерживается)
        try:
            await file.seek(0)
        except (AttributeError, OSError):
            # Если seek не поддерживается, пропускаем проверку magic bytes
            # и используем только content_type
            file_content_start = b""
            logger.debug("Seek не поддерживается, пропускаем проверку magic bytes")

        if file_content_start:
            # Проверяем magic bytes
            detected_type = None
            for magic_bytes, mime_type in IMAGE_MAGIC_BYTES.items():
                if file_content_start.startswith(magic_bytes):
                    detected_type = mime_type
                    break

            # Для WebP нужна дополнительная проверка
            if file_content_start.startswith(b"RIFF") and b"WEBP" in file_content_start:
                detected_type = "image/webp"

            # Если определен тип и он не совпадает с заявленным - предупреждение
            if detected_type and detected_type != file.content_type:
                logger.warning(
                    f"Несоответствие типа файла: заявлен {file.content_type}, "
                    f"определен {detected_type}"
                )
                # Для безопасности отклоняем несоответствие
                if detected_type not in supported_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Файл не является допустимым изображением",
                    )
    except HTTPException:
        raise
    except Exception as e:
        # Если не удалось прочитать файл, продолжаем с проверкой content_type
        logger.warning(f"Не удалось проверить magic bytes файла: {e}")

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


async def delete_uploaded_file(file_name: str, dir_location: str | None = None) -> bool:
    """Удаляет загруженный файл.

    Args:
        file_name: Имя файла для удаления
        dir_location: Директория с файлом (по умолчанию из настроек)

    Returns:
        True если файл был удален, False если файл не найден
    """
    if dir_location is None:
        dir_location = settings.UPLOAD_DIR

    file_path = Path(BASE_DIR) / dir_location / file_name

    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Файл успешно удален: {file_name}")
            return True
        else:
            logger.warning(f"Файл не найден для удаления: {file_name}")
            return False
    except OSError as e:
        logger.error(f"Ошибка при удалении файла {file_name}: {e}")
        return False
