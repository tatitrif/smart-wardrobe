"""Точка входа в приложение."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api import routers
from core.config import settings
from core.db import db_manager
from core.middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Управляет жизненным циклом приложения: инициализация и завершение работы."""
    db_manager.init()
    if settings.DATABASE_TYPE == "sqlite" and settings.ENVIRONMENT == "dev":
        await db_manager.create_all()
    yield
    await db_manager.close()


def get_app() -> FastAPI:
    """Создаёт и настраивает экземпляр FastAPI-приложения.

    Returns:
        Настроенное FastAPI-приложение с middleware, роутерами и lifespan-хуком.
    """
    _app = FastAPI(
        title=settings.PROJECT_TITLE,
        description=settings.PROJECT_DESCRIPTION,
        default_response_class=ORJSONResponse,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    _app.add_middleware(LoggingMiddleware)
    _app.include_router(routers.v1_router, prefix="/api")

    return _app


app = get_app()
