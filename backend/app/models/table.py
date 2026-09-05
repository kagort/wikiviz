from typing import List, Optional

from pydantic import BaseModel

from app.models.common import SourceType


class Table(BaseModel):
    id: str
    title: Optional[str] = None
    columns: List[str]
    rows: List[List[str]]
    source: SourceType = SourceType.TABLE