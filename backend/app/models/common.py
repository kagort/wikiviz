from enum import Enum


class EntityType(str, Enum):
    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "organization"
    EVENT = "event"
    WORK = "work"
    CONCEPT = "concept"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    INFOBOX = "infobox"
    TEMPLATE = "template"
    TABLE = "table"
    COORDINATE = "coordinate"
    ARTICLE_TEXT = "article_text"
    DERIVED = "derived"
    # зарезервировано на будущее (не используется в MVP):
    NLP = "nlp"
    WIKIDATA = "wikidata"


class DatePrecision(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    DECADE = "decade"
    CENTURY = "century"
    UNKNOWN = "unknown"