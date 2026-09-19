"""
Разведка русской разметки координат: полный href geohack-ссылки и
формат DMS с секундами (Tokyo дал только градусы+минуты, нужен пример
с секундами для полноты паттерна).

Запуск:
    python -m scripts.explore_ru_coordinates_full
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://ru.wikipedia.org/wiki/Токио",
    "https://ru.wikipedia.org/wiki/Эверест",
    "https://ru.wikipedia.org/wiki/Париж",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        coord_spans = soup.find_all("span", class_="coordinates")
        print(f"{raw.title}: найдено span.coordinates = {len(coord_spans)}")

        for span in coord_spans[:2]:
            visible_text = span.find("span", class_=None)
            print(f"  текст: {visible_text.get_text(strip=True) if visible_text else span.get_text(strip=True)!r}")

            geohack_link = span.find("a", class_="external")
            if geohack_link:
                print(f"  geohack href: {geohack_link.get('href')}")
        print()


if __name__ == "__main__":
    main()