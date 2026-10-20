"""
Происхождение значений (упрощённый Provenance, ТЗ §21; решение владельца
В2, docs/SELECTION_TZ.md): в каком разделе и в каком блоке статьи стоит
элемент HTML.

Раздел элемента - последний заголовок h2-h6 перед ним в документе.
Позиция берётся из sourceline/sourcepos, которые BeautifulSoup
(html.parser) сохраняет у тегов, поэтому поиск раздела - двоичный, без
повторного обхода документа.
"""
from bisect import bisect_right

from app.extractors.section_extractor import HEADING_TAGS, _heading_title
from app.models import BlockType, ValueContext

# Служебные разделы: даты обращения к источникам, списки литературы и
# ссылок - не содержание статьи. Их подразделы тоже служебные.
SERVICE_SECTION_TITLES = {
    "references", "citations", "bibliography", "notes", "footnotes",
    "external links", "further reading", "see also", "sources",
    "примечания", "источники", "литература", "ссылки", "см. также",
    "сноски", "примечания и источники",
}

_LIST_TAGS = {"li", "dd", "dt"}
_CAPTION_CLASSES = {"thumbcaption", "gallerytext"}


def is_service_title(title: str) -> bool:
    return title.strip().lower() in SERVICE_SECTION_TITLES


def _position(tag) -> tuple[int, int]:
    return (tag.sourceline or 0, tag.sourcepos or 0)


class SectionIndex:
    """Путь разделов для любого тега документа."""

    def __init__(self, soup):
        self._positions: list[tuple[int, int]] = []
        self._paths: list[tuple[list[str], bool]] = []
        stack: list[tuple[int, str]] = []
        for heading in soup.find_all(HEADING_TAGS):
            level = int(heading.name[1])
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, _heading_title(heading)))
            path = [title for _, title in stack]
            self._positions.append(_position(heading))
            self._paths.append((path, any(is_service_title(t) for t in path)))

    def section_of(self, tag) -> tuple[list[str], bool]:
        """(путь заголовков, служебный ли раздел) для тега; ([], False) до первого заголовка."""
        if tag is None or tag.sourceline is None:
            return [], False
        index = bisect_right(self._positions, _position(tag)) - 1
        if index < 0:
            return [], False
        path, service = self._paths[index]
        return list(path), service

    def context(self, tag, block: BlockType) -> ValueContext:
        path, service = self.section_of(tag)
        return ValueContext(block=block, section_path=path, service_section=service)


def block_of(node):
    """
    Ближайший блок текста, содержащий узел, и его вид:
    пункт списка (li/dd/dt), абзац (p), подпись иллюстрации
    (figcaption, .thumbcaption, .gallerytext), ячейка таблицы.
    Если блока нет - (родитель узла, OTHER).
    """
    for parent in node.parents:
        name = parent.name
        if name in _LIST_TAGS:
            return parent, BlockType.LIST_ITEM
        if name == "p":
            return parent, BlockType.PARAGRAPH
        if name == "figcaption" or _CAPTION_CLASSES & set(parent.get("class") or []):
            return parent, BlockType.FIGURE
        if name in ("td", "th", "table"):
            return parent, BlockType.TABLE
        if name in ("body", "[document]"):
            break
    return node.parent, BlockType.OTHER
