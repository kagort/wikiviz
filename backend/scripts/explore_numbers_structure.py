"""
Проверка гипотезы: заголовки групп внутри infobox (Area/Population/GDP)
размечены как строки с ОДНОЙ ячейкой (colspan), в отличие от обычных
label+data строк с двумя ячейками.

Запуск:
    python -m scripts.explore_numbers_structure
"""

from app.wikipedia.client import WikipediaClient
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/France"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    infobox = soup.find("table", class_="infobox")
    rows = infobox.find_all("tr")

    for row in rows[:35]:
        cells = row.find_all(["th", "td"])
        texts = [c.get_text(" ", strip=True)[:40] for c in cells]
        colspans = [c.get("colspan") for c in cells]
        print(f"cells={len(cells)}  colspan={colspans}  texts={texts}")


if __name__ == "__main__":
    main()