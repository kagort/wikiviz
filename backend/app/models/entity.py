from typing import Optional

from pydantic import BaseModel, Field

from app.models.common import EntityType, SourceType


class Entity(BaseModel):
    """Базовая абстракция сущности (§8 ТЗ). Используется для people, organizations, works."""

    id: str
    type: EntityType
    label: str
    description: Optional[str] = None
    source: SourceType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)