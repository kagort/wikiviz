"""
Диагностика двух новых находок: структура секции GDP (не через
infobox-header) и разметка координат в русской Wikipedia.

Запуск:
    python -m scripts.diagnose_numbers_edge_cases
"""

from app.wikipedia.client import WikipediaClient
from bs4 import BeautifulSoup


def diagnose_gdp_structure() -> None:
    print("=" * 70)
    print("FRANCE (en) — строки вокруг GDP")
    print("=" * 70)

    client = WikipediaClient()
    raw = client.fetch_article("https://en.wikipedia.org/wiki/France")
    soup = BeautifulSoup(raw.html, "html.parser")
    infobox = soup.find("table", class_="infobox")

    rows = infobox.find_all("tr")
    printing = False
    for row in rows:
        cells = row.find_all(["th", "td"])
        text_preview = " | ".join(c.get_text(" ", strip=True)[:30] for c in cells)
        if "GDP" in text_preview:
            printing = True
        if printing:
            classes = [c.get("class") for c in cells]
            print(f"cells={len(cells)} class={classes} text={text_preview!r}")
        if printing and "Gini" in text_preview:
            break


def diagnose_ru_coordinates() -> None:
    print()
    print("=" * 70)
    print("ТОКИО (ru) — строка координат")
    print("=" * 70)

    client = WikipediaClient()
    raw = client.fetch_article("https://ru.wikipedia.org/wiki/Токио")
    soup = BeautifulSoup(raw.html, "html.parser")
    infobox = soup.find("table", class_="infobox")

    for row in infobox.find_all("tr"):
        cells = row.find_all(["th", "td"])
        text_preview = " | ".join(c.get_text(" ", strip=True)[:40] for c in cells)
        if "оордин" in text_preview.lower() or "35°" in text_preview:
            print(f"raw row html (первые 500 симв.): {str(row)[:500]}")


if __name__ == "__main__":
    diagnose_gdp_structure()
    diagnose_ru_coordinates()