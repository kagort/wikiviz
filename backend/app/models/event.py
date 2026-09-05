from typing import Optional

from pydantic import BaseModel, Field

from app.models.common import DatePrecision, SourceType


class Event(BaseModel):
    id: str
    date: str  # хранится как строка ISO ("1879-03-14" или "-0044-03-15" для дат до н.э.)
    date_precision: DatePrecision
    title: str
    description: Optional[str] = None
    source: SourceType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)