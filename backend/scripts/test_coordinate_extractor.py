"""
Ручной интеграционный скрипт: CoordinateExtractor на реальных статьях
разных типов (гора, река, село, остров, статья с несколькими координатами).

Запуск (из папки backend, venv активен):
    python -m scripts.test_coordinate_extractor
"""

from app.extractors.coordinate_extractor import extract_coordinates
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://en.wikipedia.org/wiki/Mount_Everest",
    "https://en.wikipedia.org/wiki/Nile",
    "https://en.wikipedia.org/wiki/Stow-on-the-Wold",
    "https://en.wikipedia.org/wiki/Isle_of_Skye",
    "https://en.wikipedia.org/wiki/Seven_Summits",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)
        locations = extract_coordinates(raw.html, article_title=raw.title)

        print(f"{raw.title}: найдено координат = {len(locations)}")
        for loc in locations[:3]:
            print(f"  [{loc.id}] {loc.name!r}: lat={loc.latitude}, lon={loc.longitude}")
        print()


if __name__ == "__main__":
    main()