from typing import Optional

from pydantic import BaseModel

from app.models.common import SourceType


class Image(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    alt: Optional[str] = None
    source: SourceType = SourceType.ARTICLE_TEXT