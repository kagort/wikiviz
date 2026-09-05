from typing import Optional

from pydantic import BaseModel, Field

from app.models.common import SourceType


class Location(BaseModel):
    id: str
    name: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    description: Optional[str] = None
    source: SourceType = SourceType.COORDINATE
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)