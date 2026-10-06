from typing import Optional

from pydantic import BaseModel

from app.models.common import SourceType


class InfoboxField(BaseModel):
    """
    Одно поле инфобокса (§11 ТЗ), например 'Born: 14 March 1879'.

    group - подзаголовок, к которому относится поле ("Area" для
    "• Total" у France), или None для поля верхнего уровня. Без него
    одинаковые подписи ("Total" у площади и у ВВП) неразличимы.
    """

    key: str
    label: str
    group: Optional[str] = None
    value: str
    normalized_value: Optional[str] = None
    source: SourceType = SourceType.INFOBOX