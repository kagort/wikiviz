"""
Разведочный скрипт: показывает устройство infobox'ов статей манифеста.

Для каждой статьи печатает число <table class="infobox"> (и вложенных),
затем строки первого infobox'а: число ячеек, теги, классы и текст
первых двух ячеек, а также служебную разметку внутри значения
(сноски, скрытые span'ы, списки, <br>). Нужен для InfoboxExtractor.

Запуск (из папки backend):
    python -m scripts.inspect_infobox                   # все статьи манифеста
    python -m scripts.inspect_infobox socrates-ru.json  # только выбранные
"""
import collections
import sys

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient
from scripts.export_fixtures import MANIFEST_PATH, load_manifest


def _short(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _markers(cell) -> str:
    marks = []
    if cell.find("sup", class_="reference"):
        marks.append("ref")
    if cell.find(style=lambda s: s and "display:none" in s.replace(" ", "")):
        marks.append("hidden")
    if cell.find(["ul", "ol"]):
        marks.append("list")
    if cell.find("br"):
        marks.append("br")
    if cell.find("table"):
        marks.append("table")
    if cell.find("img"):
        marks.append("img")
    return ",".join(marks)


def inspect(html: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    infoboxes = soup.find_all("table", class_="infobox")
    nested = [t for t in infoboxes if t.find_parent("table", class_="infobox")]
    print(f"  infobox tables: {len(infoboxes)} (nested inside another: {len(nested)})")
    for table in infoboxes:
        print(f"    classes: {' '.join(table.get('class', []))}")
    if not infoboxes:
        return

    infobox = infoboxes[0]
    labels = collections.Counter()
    for row in infobox.find_all("tr"):
        if row.find_parent("table") is not infobox:
            continue  # строка вложенной таблицы
        cells = row.find_all(["th", "td"], recursive=False)
        shape = "+".join(
            f"{c.name}.{(c.get('class') or ['-'])[0]}" for c in cells
        )
        if len(cells) >= 2:
            labels[_short(cells[0].get_text(" "), 40)] += 1
            print(
                f"    [{len(cells)}] {shape:40} "
                f"{_short(cells[0].get_text(' '), 30)!r:34} = "
                f"{_short(cells[1].get_text(' '))!r} {_markers(cells[1])}"
            )
        elif cells:
            print(f"    [1] {shape:40} {_short(cells[0].get_text(' '))!r} {_markers(cells[0])}")
    repeated = {label: n for label, n in labels.items() if n > 1}
    print(f"  repeated labels: {repeated or 'none'}")


def main() -> None:
    wanted = set(sys.argv[1:])
    client = WikipediaClient()
    for entry in load_manifest(MANIFEST_PATH):
        if wanted and entry.file not in wanted:
            continue
        print(f"\n=== {entry.url} (revision {entry.revision}) ===")
        raw = client.fetch_article(entry.url, revision_id=entry.revision)
        inspect(raw.html)


if __name__ == "__main__":
    main()
