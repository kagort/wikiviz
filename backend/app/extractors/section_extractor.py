from bs4 import BeautifulSoup
from pydantic import BaseModel

HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6"]


class ArticleSection(BaseModel):
    """Структурированный раздел статьи, извлечённый из HTML.

    Внутренняя рабочая структура этого extractor'а - не часть публичного
    контракта NormalizedArticleModel (см. app/models/). Хранит сырой HTML,
    который будет использован на следующем шаге нормализации.
    """

    level: int
    title: str
    html: str


def extract_sections(html: str) -> list[ArticleSection]:
    """
    Разбивает HTML статьи на разделы по заголовкам h2-h6.

    Правило: раздел начинается с заголовка и продолжается до следующего
    заголовка любого уровня. Контент до первого заголовка игнорируется.

    Поддерживает два варианта разметки:
      - обычный: <h2>Title</h2><p>...</p>
      - MediaWiki-обертка: <div class="mw-heading mw-heading2"><h2>Title</h2>...</div><p>...</p>
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    headings = soup.find_all(HEADING_TAGS)

    if not headings:
        return []

    boundaries = []
    for heading in headings:
        wrapper = heading.find_parent("div", class_="mw-heading")
        boundary_element = wrapper if wrapper is not None else heading
        level = int(heading.name[1])
        title = heading.get_text(strip=True)
        boundaries.append((boundary_element, level, title))

    sections = []
    for index, (boundary_element, level, title) in enumerate(boundaries):
        next_boundary = boundaries[index + 1][0] if index + 1 < len(boundaries) else None

        content_parts = []
        sibling = boundary_element.next_sibling
        while sibling is not None and sibling is not next_boundary:
            if getattr(sibling, "name", None) is not None:
                content_parts.append(str(sibling))
            sibling = sibling.next_sibling

        sections.append(
            ArticleSection(
                level=level,
                title=title,
                html="".join(content_parts),
            )
        )

    return sections
