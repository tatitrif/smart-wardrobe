"""Middleware для безопасного логирования, трейсинга и замера времени обработки."""

import contextvars
import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from .logger import setup_logger

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

logger = setup_logger(__name__)

# Настройки безопасности
SENSITIVE_PATHS = {"/token", "/login", "/auth", "/register"}
SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "x-secret"}


def mask_sensitive_data(data: Any) -> Any:
    """Рекурсивно маскирует чувствительные поля."""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(
                s in key_lower for s in ("password", "secret", "token", "key", "auth")
            ):
                masked[key] = "***MASKED***"
            else:
                masked[key] = mask_sensitive_data(value)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def mask_headers(headers: dict) -> dict:
    """Маскирует чувствительные заголовки."""
    return {
        k: ("***MASKED***" if k.lower() in SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }


async def safe_get_body(request: Request, is_sensitive: bool) -> str | None:
    """Безопасно извлекает и маскирует тело запроса."""
    if is_sensitive or request.method not in ("POST", "PUT", "PATCH"):
        return None

    try:
        body_bytes = await request.body()
        if not body_bytes:
            return None

        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body_dict = json.loads(body_bytes.decode())
            return json.dumps(mask_sensitive_data(body_dict), ensure_ascii=False)
        else:
            return "***NON-JSON BODY***"
    except Exception:
        return "***FAILED TO PARSE BODY***"


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования HTTP-запросов с поддержкой распределённого трейсинга.

    Обеспечивает:
    - Генерацию и прокидывание trace_id (X-Request-ID),
    - Маскировку чувствительных данных (пароли, токены),
    - Замер времени обработки запроса (X-Process-Time),
    - Структурированное логирование в JSON (в продакшене).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает входящий запрос и логирует его до и после выполнения.

        Args:
            request: Входящий HTTP-запрос.
            call_next: Следующий обработчик в цепочке middleware.

        Returns:
            HTTP-ответ после обработки.

        Raises:
            Любое исключение, возникшее при обработке запроса.
        """
        trace_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request_id_ctx.set(trace_id)
        path = request.url.path
        is_sensitive = any(path.startswith(p) for p in SENSITIVE_PATHS)
        start_time = time.time()

        # Логирование запроса
        log_data = {
            "trace_id": trace_id,
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "headers": mask_headers(dict(request.headers)),
        }

        if not is_sensitive:
            log_data["body"] = await safe_get_body(request, is_sensitive)

        logger.info("Входящий запрос", extra=log_data)

        # Обработка запроса
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Ошибка при обработке запроса",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

        # Финализация
        duration = time.time() - start_time
        duration_sec = round(duration, 4)

        # Добавляем заголовоки
        response.headers["X-Process-Time"] = str(duration_sec)
        response.headers["X-Request-ID"] = trace_id

        # Логирование ответа
        response_log = {
            "trace_id": trace_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "process_time_sec": duration_sec,  # то же самое, но в секундах
        }

        if not is_sensitive and not isinstance(response, StreamingResponse):
            try:
                body = getattr(response, "body", b"")
                if body and (body.startswith(b"{") or body.startswith(b"[")):
                    body_dict = json.loads(body)
                    response_log["response_body"] = json.dumps(
                        mask_sensitive_data(body_dict), ensure_ascii=False
                    )
            except Exception as e:
                logger.warning(
                    "Не удалось замаскировать или распарсить тело ответа: ", extra=e
                )

        logger.info("Исходящий ответ", extra=response_log)

        return response
