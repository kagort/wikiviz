from typing import Optional

from pydantic import BaseModel

from app.models.common import SourceType
from app.models.context import ValueContext


class NumericValue(BaseModel):
    label: str
    value: float
    unit: Optional[str] = None
    year: Optional[int] = None
    source: SourceType
    context: Optional[ValueContext] = None