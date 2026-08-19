from enum import Enum

from pydantic import BaseModel


class EntityType(str, Enum):
    PERSON = "Person"
    LOCATION = "Location"
    ORGANIZATION = "Organization"
    EVENT = "Event"
    WORK = "Work"
    CONCEPT = "Concept"
    UNKNOWN = "Unknown"


class Entity(BaseModel):
    type: EntityType
    name: str