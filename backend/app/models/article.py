from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Article(BaseModel):
    id: int
    title: str
    language: str
    url: str
    description: Optional[str] = None
    summary: Optional[str] = None


class Section(BaseModel):
    """Дерево разделов статьи (§15 ТЗ)."""

    id: str
    title: str
    level: int
    children: List["Section"] = []


Section.model_rebuild()