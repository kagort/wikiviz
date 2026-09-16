"""
Разведка: полная структура строки таблицы с координатой в Seven Summits —
чтобы понять, откуда взять название горы для каждой координаты.

Запуск:
    python -m scripts.explore_seven_summits_row
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

URL = "https://en.wikipedia.org/wiki/Seven_Summits"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    lat_spans = soup.find_all(class_="latitude")

    # Берём первую координату и печатаем HTML всей строки таблицы целиком
    first_lat = lat_spans[0]
    row = first_lat.find_parent("tr")

    print("Полный HTML строки:")
    print(row.prettify()[:2000])
    print()

    print("Все ячейки строки и их текст:")
    for i, cell in enumerate(row.find_all(["th", "td"])):
        print(f"  [{i}] tag={cell.name}: {cell.get_text(strip=True)!r}")


if __name__ == "__main__":
    main()