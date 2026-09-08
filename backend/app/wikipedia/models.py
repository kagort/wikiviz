from typing import Optional

from pydantic import BaseModel


class RawArticle(BaseModel):
    """Сырые данные статьи, полученные от MediaWiki API — ещё не наша Normalized-модель."""

    page_id: int
    title: str
    language: str
    url: str
    html: str
    revision_id: Optional[int] = None