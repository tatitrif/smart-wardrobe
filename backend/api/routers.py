"""FastAPI route definitions."""

from fastapi import APIRouter

from .v1 import items
from .v1 import item_image
from .v1 import item_recognition

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(items.router)
v1_router.include_router(item_image.router)
v1_router.include_router(item_recognition.router)
