"""Конфигурация приложения через Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, AnyUrl
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


class Settings(BaseSettings):
    """Настройки приложения с поддержкой переменных окружения и .env-файлов."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    # Проект
    PROJECT_TITLE: str = "Smart Wardrobe API"
    PROJECT_DESCRIPTION: str = "Управления предметами гардероба."
    VERSION: str = "0.1.0"

    # Сервер
    PORT: int = 8000
    RELOAD: bool = False

    # Настройки окружения
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    DEBUG: bool = False

    # Выбор БД: "sqlite" или "postgres"
    DATABASE_TYPE: Literal["sqlite", "postgres"] = "sqlite"

    # SQLite
    SQLITE_PATH: str = "database.db"

    # PostgreSQL
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres_db"

    # Настройки загрузки файлов
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB в байтах
    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    ]

    @property
    def DATABASE_URL(self) -> AnyUrl:
        """Формирует URL подключения к базе данных в зависимости от типа БД."""
        if self.DATABASE_TYPE == "sqlite":
            return AnyUrl(f"sqlite+aiosqlite:///{self.SQLITE_PATH}")
        else:
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )


@lru_cache(maxsize=1)
def get_settings():
    """Возвращает экземпляр настроек с кэшированием."""
    return Settings()  # noqa


settings = get_settings()
