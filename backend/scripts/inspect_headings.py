"""
Разведочный скрипт: показывает, где в HTML статьи лежит каждый заголовок h2-h6.

Для каждого заголовка печатает уровень, текст, обёрнут ли он в
div.mw-heading и цепочку «значимых» предков (классы navbox, sidebar,
infobox, role=navigation и т. п.). Нужен, чтобы отличить настоящие
разделы статьи от заголовков внутри навигационных блоков.

Статьи и ревизии берутся из манифеста фикстур, поэтому результат
воспроизводим.

Запуск (из папки backend):
    python -m scripts.inspect_headings                # все статьи манифеста
    python -m scripts.inspect_headings france.json    # только выбранные
"""
import sys

from bs4 import BeautifulSoup

from app.extractors.section_extractor import HEADING_TAGS, _heading_title
from app.wikipedia.client import WikipediaClient
from scripts.export_fixtures import MANIFEST_PATH, load_manifest

INTERESTING_CLASSES = (
    "navbox", "navbox-inner", "navbox-subgroup", "vertical-navbox",
    "sidebar", "infobox", "metadata", "noprint", "reflist", "refbegin",
    "mw-collapsible", "hlist", "sistersitebox", "side-box", "ambox",
    "navigation-not-searchable", "thumb", "gallery",
)


def _describe(element) -> str:
    classes = element.get("class", [])
    marks = [c for c in classes if c in INTERESTING_CLASSES or c.startswith("navbox")]
    role = element.get("role")
    if role:
        marks.append(f"role={role}")
    if not marks:
        return ""
    return f"{element.name}[{' '.join(marks)}]"


def inspect(html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_="mw-parser-output") or soup

    for heading in root.find_all(HEADING_TAGS):
        wrapped = heading.find_parent("div", class_="mw-heading") is not None
        chain = [
            d for d in (_describe(p) for p in heading.parents if p is not root and p.name)
            if d
        ]
        # «Верхний уровень»: заголовок (или его обёртка) - прямой потомок корня.
        top = heading.find_parent("div", class_="mw-heading") or heading
        direct = top.parent is root
        print(
            f"  h{heading.name[1]} {'W' if wrapped else '-'} "
            f"{'top ' if direct else 'deep'} {_heading_title(heading)!r:45} "
            f"{' < '.join(chain)}"
        )


def main() -> None:
    wanted = set(sys.argv[1:])
    client = WikipediaClient()
    for entry in load_manifest(MANIFEST_PATH):
        if wanted and entry.file not in wanted:
            continue
        print(f"\n=== {entry.url} (revision {entry.revision}) ===")
        print("  legend: W = inside div.mw-heading; top = direct child of article root")
        raw = client.fetch_article(entry.url, revision_id=entry.revision)
        inspect(raw.html)


if __name__ == "__main__":
    main()
