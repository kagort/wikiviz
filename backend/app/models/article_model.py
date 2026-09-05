from typing import Any, Dict, List

from pydantic import BaseModel

from app.models.article import Article, Section
from app.models.entity import Entity
from app.models.event import Event
from app.models.image import Image
from app.models.infobox import InfoboxField
from app.models.location import Location
from app.models.number import NumericValue
from app.models.table import Table


class NormalizedArticleModel(BaseModel):
    """Единый контракт между backend и frontend (§7 ТЗ)."""

    article: Article
    sections: List[Section] = []
    infobox: Dict[str, InfoboxField] = {}
    tables: List[Table] = []
    locations: List[Location] = []
    events: List[Event] = []
    numbers: List[NumericValue] = []
    people: List[Entity] = []
    organizations: List[Entity] = []
    works: List[Entity] = []
    relations: List[Dict[str, Any]] = []  # заглушка под 2.x, форма ещё не зафиксирована
    images: List[Image] = []
    links: List[str] = []
    metadata: Dict[str, Any] = {}