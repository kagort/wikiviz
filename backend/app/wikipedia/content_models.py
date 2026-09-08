from pydantic import BaseModel


class ArticleSection(BaseModel):
    """Структурированный раздел статьи."""

    level: int
    title: str
    html: str


class ParsedArticle(BaseModel):
    """Структурированное представление содержимого статьи."""

    title: str
    language: str
    url: str
    sections: list[ArticleSection]