from typing import Optional

from pydantic import BaseModel

from app.models.common import SourceType


class InfoboxField(BaseModel):
    """Одно поле инфобокса (§11 ТЗ), например 'Born: 14 March 1879'."""

    key: str
    label: str
    value: str
    normalized_value: Optional[str] = None
    source: SourceType = SourceType.INFOBOX