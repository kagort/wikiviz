from bs4 import BeautifulSoup

from app.wikipedia.content_models import ArticleSection


def extract_sections(html: str) -> list[ArticleSection]:
    """
    Извлекает разделы статьи из HTML.

    Раздел начинается с заголовка h2–h6 и продолжается
    до следующего заголовка любого уровня.

    Поддерживает как обычные заголовки:

        <h2>History</h2>

    так и структуру MediaWiki:

        <div class="mw-heading mw-heading2">
            <h2>History</h2>
            ...
        </div>

    Контент до первого заголовка игнорируется.
    """

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    sections: list[ArticleSection] = []

    headings = soup.find_all(["h2", "h3", "h4", "h5", "h6"])

    for index, heading in enumerate(headings):
        level = int(heading.name[1])
        title = heading.get_text(strip=True)

        # MediaWiki помещает заголовок внутрь специального
        # контейнера <div class="mw-heading ...">.
        # В обычном HTML заголовок сам является границей раздела.
        parent = heading.parent

        is_mediawiki_wrapper = (
            getattr(parent, "name", None) == "div"
            and "mw-heading" in parent.get("class", [])
        )

        if is_mediawiki_wrapper:
            start_node = parent
        else:
            start_node = heading

        # Следующий заголовок также может находиться
        # внутри MediaWiki-wrapper.
        next_heading = (
            headings[index + 1]
            if index + 1 < len(headings)
            else None
        )

        if next_heading is not None:
            next_parent = next_heading.parent

            next_is_mediawiki_wrapper = (
                getattr(next_parent, "name", None) == "div"
                and "mw-heading" in next_parent.get("class", [])
            )

            if next_is_mediawiki_wrapper:
                end_node = next_parent
            else:
                end_node = next_heading
        else:
            end_node = None

        content: list[str] = []

        for sibling in start_node.next_siblings:
            if sibling is end_node:
                break

            if getattr(sibling, "name", None) is not None:
                content.append(str(sibling))

        sections.append(
            ArticleSection(
                level=level,
                title=title,
                html="".join(content).strip(),
            )
        )

    return sections