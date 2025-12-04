"""Модуль для распознавания одежды на изображениях."""

import asyncio
import json
from pathlib import Path

from core.config import settings
from core.logger import setup_logger

logger = setup_logger(__name__)


class RecognitionResult:
    """Результат распознавания одежды на изображении."""

    def __init__(  # noqa
        self,
        category: str | None = None,
        name: str | None = None,
        brand: str | None = None,
        material: str | None = None,
        pattern: str | None = None,
        dominant_color: str | None = None,
        color_palette: list[str] | None = None,
        season: list[str] | None = None,
        occasion: list[str] | None = None,
        confidence: float = 0.0,
    ):
        self.category = category
        self.name = name
        self.brand = brand
        self.material = material
        self.pattern = pattern
        self.dominant_color = dominant_color
        self.color_palette = color_palette or []
        self.season = season or []
        self.season = season or []
        self.occasion = occasion or []
        self.confidence = confidence


async def recognize_clothing_from_image(
    image_path: Path | str,
) -> RecognitionResult:
    """Распознает одежду на изображении.

    Args:
        image_path: Путь к файлу изображения

    Returns:
        RecognitionResult с распознанными данными

    """
    image_path = Path(image_path)

    if not image_path.exists():
        logger.error(f"Файл изображения не найден: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    service = settings.RECOGNITION_SERVICE
    logger.info(
        "Распознавание одежды на изображении %s (service=%s)",
        image_path.name,
        service,
    )

    if service == "local":
        result = await _recognize_with_local_model(image_path)
    elif service == "mock":
        result = await _mock_recognition(image_path)
    else:
        # Пока поддерживаем только mock/local. Остальные сервисы можно добавить позже.
        logger.warning(
            "Неизвестный тип сервиса распознавания '%s'. Использую mock.", service
        )
        result = await _mock_recognition(image_path)

    return result


async def _mock_recognition(image_path: Path) -> RecognitionResult:
    """Mock-реализация распознавания одежды.

    В реальном приложении здесь должна быть интеграция с ML моделью или API.
    """
    # Простая эвристика на основе имени файла или размера
    filename = image_path.name.lower()

    # Определение категории по имени файла
    category = None
    if any(word in filename for word in ["shirt", "рубашка", "футболка"]):
        category = "shirt"
    elif any(word in filename for word in ["pants", "брюки", "джинсы"]):
        category = "pants"
    elif any(word in filename for word in ["dress", "платье"]):
        category = "dress"
    elif any(word in filename for word in ["jacket", "куртка", "пиджак"]):
        category = "jacket"
    elif any(word in filename for word in ["shoes", "обувь", "кроссовки"]):
        category = "shoes"
    else:
        category = "other"

    # Генерация имени на основе категории
    category_names = {
        "shirt": "Футболка",
        "pants": "Брюки",
        "dress": "Платье",
        "jacket": "Куртка",
        "shoes": "Обувь",
        "other": "Предмет гардероба",
    }
    name = category_names.get(category, "Предмет гардероба")

    # Mock данные
    return RecognitionResult(
        category=category,
        name=name,
        brand=None,  # Можно попытаться распознать по логотипу
        material=None,  # Требует специального анализа
        pattern="solid",  # По умолчанию
        dominant_color="#808080",  # Серый по умолчанию
        color_palette=["#808080"],
        season=["spring", "summer", "autumn", "winter"],  # Универсальный
        occasion=["casual"],
        confidence=0.7,  # Mock уверенность
    )


async def _recognize_with_local_model(image_path: Path) -> RecognitionResult:
    """Выполняет распознавание при помощи локальной ML модели (YOLO, TensorFlow и т.п.).

    Ожидается, что в настройке RECOGNITION_LOCAL_COMMAND указан шаблон команды запуска,
    например::

        RECOGNITION_LOCAL_COMMAND="python scripts/infer.py --image {image}"

    Команда должна вернуть JSON следующего вида:
    {
        "category": "shirt",
        "name": "Футболка",
        "brand": "Nike",
        "material": "cotton",
        "pattern": "solid",
        "dominant_color": "#FFCC00",
        "color_palette": ["#FFCC00", "#000000"],
        "season": ["summer"],
        "occasion": ["sport"],
        "confidence": 0.92
    }
    """
    command_template = settings.RECOGNITION_LOCAL_COMMAND
    if not command_template:
        raise RuntimeError(
            "RECOGNITION_LOCAL_COMMAND не задан. Укажите команду запуска локальной ML модели."
        )

    command = command_template.format(image=str(image_path))
    logger.debug("Запуск локальной модели: %s", command)

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=settings.RECOGNITION_LOCAL_TIMEOUT
        )
    except TimeoutError as exc:
        process.kill()
        logger.error(
            "Локальная модель превысила таймаут (%s сек)",
            settings.RECOGNITION_LOCAL_TIMEOUT,
        )
        raise RuntimeError("Локальная модель превысила таймаут") from exc

    if process.returncode != 0:
        logger.error(
            "Локальная модель завершилась с ошибкой (%s): %s",
            process.returncode,
            stderr.decode("utf-8", errors="ignore"),
        )
        raise RuntimeError("Не удалось выполнить локальное распознавание")

    stdout_text = stdout.decode("utf-8").strip()
    if not stdout_text:
        raise RuntimeError("Локальная модель вернула пустой ответ")

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        logger.error("Локальная модель вернула невалидный JSON: %s", stdout_text)
        raise RuntimeError("Локальная модель вернула невалидный JSON") from exc

    result = _map_payload_to_result(payload)

    if (
        result.confidence
        and result.confidence < settings.RECOGNITION_LOCAL_CONFIDENCE_THRESHOLD
    ):
        logger.warning(
            "Распознавание ниже порога доверия (%.2f < %.2f)",
            result.confidence,
            settings.RECOGNITION_LOCAL_CONFIDENCE_THRESHOLD,
        )

    return result


def _map_payload_to_result(payload: dict) -> RecognitionResult:
    """Преобразует JSON, полученный от локальной модели, в RecognitionResult."""
    return RecognitionResult(
        category=payload.get("category"),
        name=payload.get("name"),
        brand=payload.get("brand"),
        material=payload.get("material"),
        pattern=payload.get("pattern"),
        dominant_color=payload.get("dominant_color"),
        color_palette=payload.get("color_palette") or [],
        season=payload.get("season") or [],
        occasion=payload.get("occasion") or [],
        confidence=float(payload.get("confidence") or 0.0),
    )


async def recognize_clothing_from_multiple_images(
    image_paths: list[Path | str],
) -> RecognitionResult:
    """Распознает одежду на основе нескольких изображений.

    Агрегирует результаты распознавания с нескольких фото для более точного результата.

    Args:
        image_paths: Список путей к файлам изображений

    Returns:
        RecognitionResult с агрегированными данными
    """
    if not image_paths:
        raise ValueError("Список изображений не может быть пустым")

    results = []
    for image_path in image_paths:
        try:
            result = await recognize_clothing_from_image(image_path)
            results.append(result)
        except Exception as e:
            logger.warning(f"Ошибка при распознавании {image_path}: {e}")
            continue

    if not results:
        raise ValueError("Не удалось распознать ни одно изображение")

    # Агрегация результатов
    return _aggregate_recognition_results(results)


def _aggregate_recognition_results(
    results: list[RecognitionResult],
) -> RecognitionResult:
    """Агрегирует результаты распознавания с нескольких изображений.

    Использует голосование большинством для категории и других полей.
    """
    if not results:
        raise ValueError("Список результатов пуст")

    # Голосование по категории
    categories = [r.category for r in results if r.category]
    category = max(set(categories), key=categories.count) if categories else None

    # Голосование по имени
    names = [r.name for r in results if r.name]
    name = max(set(names), key=names.count) if names else None

    # Объединение уникальных значений для списков
    all_brands = [r.brand for r in results if r.brand]
    brand = all_brands[0] if all_brands else None

    all_materials = [r.material for r in results if r.material]
    material = all_materials[0] if all_materials else None

    all_patterns = [r.pattern for r in results if r.pattern]
    pattern = max(set(all_patterns), key=all_patterns.count) if all_patterns else None

    # Объединение цветов
    all_colors = []
    for r in results:
        if r.dominant_color:
            all_colors.append(r.dominant_color)
        if r.color_palette:
            all_colors.extend(r.color_palette)

    dominant_color = all_colors[0] if all_colors else None
    color_palette = list(set(all_colors))[:5] if all_colors else []  # Максимум 5 цветов

    # Объединение сезонов и поводов
    all_seasons = []
    all_occasions = []
    for r in results:
        if r.season:
            all_seasons.extend(r.season)
        if r.occasion:
            all_occasions.extend(r.occasion)

    season = list(set(all_seasons)) if all_seasons else []
    occasion = list(set(all_occasions)) if all_occasions else []

    # Средняя уверенность
    confidences = [r.confidence for r in results if r.confidence > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return RecognitionResult(
        category=category,
        name=name,
        brand=brand,
        material=material,
        pattern=pattern,
        dominant_color=dominant_color,
        color_palette=color_palette,
        season=season,
        occasion=occasion,
        confidence=avg_confidence,
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Конвертирует RGB в HEX формат."""
    return f"#{r:02x}{g:02x}{b:02x}".upper()
