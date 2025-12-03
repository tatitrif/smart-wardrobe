"""Асинхронное управление подключением к БД с поддержкой тестов."""

from collections.abc import AsyncGenerator

from models import DeclarativeBaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from .config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная сессия, используется как зависимость через Depends(get_db)."""
    async for session in db_manager.session():
        yield session


class DatabaseSessionManager:
    """Менеджер асинхронных сессий базы данных с поддержкой тестов."""

    def __init__(self) -> None:
        """Инициализирует менеджер без подключения к базе данных."""
        self._engine: AsyncEngine | None = None
        self._sessionmaker: sessionmaker | None = None

    def init(self, database_url: str | None = None) -> None:
        """Инициализирует движок и фабрику сессий.

        Args:
            database_url: Переопределяет URL из настроек (полезно для тестов).
        """
        db_url = database_url or str(settings.DATABASE_URL)
        self._engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        )
        self._sessionmaker = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Закрывает подключение к базе данных и освобождает ресурсы."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @property
    def sessionmaker(self) -> sessionmaker:
        """Возвращает фабрику сессий SQLAlchemy."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        return self._sessionmaker

    @property
    def engine(self) -> AsyncEngine:
        """Возвращает асинхронный движок SQLAlchemy."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        return self._engine

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Предоставляет асинхронную сессию как генератор."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        async with self._sessionmaker() as session:
            yield session

    async def create_all(self) -> None:
        """Создаёт все таблицы (только для тестов или dev)."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        async with self._engine.begin() as conn:
            await conn.run_sync(DeclarativeBaseModel.metadata.create_all)

    async def drop_all(self) -> None:
        """Удаляет все таблицы (только для тестов)."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager не инициализирован")
        async with self._engine.begin() as conn:
            await conn.run_sync(DeclarativeBaseModel.metadata.drop_all)


# Глобальный экземпляр
db_manager = DatabaseSessionManager()
