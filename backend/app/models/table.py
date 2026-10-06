from typing import List, Optional

from pydantic import BaseModel

from app.models.common import SourceType


class Table(BaseModel):
    """
    Таблица с данными (§12 ТЗ).

    notes - строки таблицы во всю ширину, не являющиеся данными:
    пояснение над шапкой (если название уже есть в caption) и
    примечания под данными ("Источник: ..."). Хранятся отдельно,
    чтобы не попадать в rows и не теряться.
    """

    id: str
    title: Optional[str] = None
    columns: List[str]
    rows: List[List[str]]
    notes: List[str] = []
    source: SourceType = SourceType.TABLE