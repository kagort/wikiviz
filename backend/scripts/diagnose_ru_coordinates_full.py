"""
Уточнение: полная структура координатной строки в русской Wikipedia -
предыдущий вывод был обрезан на самом интересном месте.

Запуск:
    python -m scripts.diagnose_ru_coordinates_full
"""

from app.wikipedia.client import WikipediaClient
from bs4 import BeautifulSoup

client = WikipediaClient()
raw = client.fetch_article("https://ru.wikipedia.org/wiki/Токио")
soup = BeautifulSoup(raw.html, "html.parser")
infobox = soup.find("table", class_="infobox")

for row in infobox.find_all("tr"):
    cells = row.find_all(["th", "td"])
    text_preview = " | ".join(c.get_text(" ", strip=True)[:40] for c in cells)
    if "35°" in text_preview:
        data_cell = cells[-1]
        print("Классы всех вложенных span/a внутри data-ячейки:")
        for el in data_cell.find_all(["span", "a"]):
            print(f"  <{el.name} class={el.get('class')}> text={el.get_text(strip=True)[:40]!r}")