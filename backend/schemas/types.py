"""Типы и перечисления, используемые в схемах API.

Содержи повторно используемые типы, применяемые в Pydantic-моделях и эндпоинтах.
"""

from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

# Определяем тип для HEX-цвета
HexColorStr = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]
IDType = UUID
# AngleType = Literal["front", "back", "label", "detail"]
AngleStr = Annotated[str, StringConstraints(pattern="^(front|back|label|detail)$")]
