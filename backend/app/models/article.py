from pydantic import BaseModel, HttpUrl

class Article(BaseModel):
    id: int | None = None
    title: str
    language: str
    url: HttpUrl
    description: str | None = None
    summary: str | None = None