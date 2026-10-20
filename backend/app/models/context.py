from enum import Enum
from typing import List

from pydantic import BaseModel


class BlockType(str, Enum):
    """Вид блока статьи, из которого извлечено значение."""

    INFOBOX = "infobox"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"  # иллюстрация в тексте или её подпись
    GALLERY = "gallery"
    OTHER = "other"


class ValueContext(BaseModel):
    """
    Происхождение значения в статье (упрощённый Provenance, ТЗ §21;
    решение владельца В2, docs/SELECTION_TZ.md). Нужен слою отбора
    надёжных данных: например, даты из пунктов списков почти всегда шум.

    section_path - заголовки разделов от верхнего уровня к вложенному
    ([] - до первого заголовка, в том числе инфобокс);
    service_section - значение внутри служебного раздела (литература,
    ссылки, примечания...) или его подраздела.
    """

    block: BlockType
    section_path: List[str] = []
    service_section: bool = False
