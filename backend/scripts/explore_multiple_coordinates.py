"""
Разведка: ищем статью с несколькими координатами в одной странице
(например, список вершин с координатами каждой в таблице).

Запуск:
    python -m scripts.explore_multiple_coordinates
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

# Список статей-кандидатов на множественные координаты
CANDIDATES = [
    "https://en.wikipedia.org/wiki/Seven_Summits",
    "https://en.wikipedia.org/wiki/List_of_rivers_of_France",
    "https://en.wikipedia.org/wiki/Great_Lakes",
]


def main() -> None:
    client = WikipediaClient()

    for url in CANDIDATES:
        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        lat_spans = soup.find_all(class_="latitude")
        lon_spans = soup.find_all(class_="longitude")

        print(f"{raw.title}: latitude spans = {len(lat_spans)}, longitude spans = {len(lon_spans)}")

        if len(lat_spans) > 1:
            print("  Первые 3 пары:")
            for lat, lon in list(zip(lat_spans, lon_spans))[:3]:
                print(f"    lat={lat.get_text(strip=True)!r}  lon={lon.get_text(strip=True)!r}")
                # Смотрим, есть ли рядом (в той же строке таблицы) текст-название
                row = lat.find_parent("tr")
                if row:
                    first_cell = row.find(["th", "td"])
                    print(f"    возможное название (первая ячейка строки): {first_cell.get_text(strip=True) if first_cell else None!r}")
        print()


if __name__ == "__main__":
    main()