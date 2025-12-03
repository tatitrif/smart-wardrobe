"""FastAPI route definitions."""

from fastapi import APIRouter

from .v1 import items

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(items.router)
