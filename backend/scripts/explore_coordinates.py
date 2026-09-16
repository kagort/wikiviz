"""
Разведочный скрипт: изучает, как реально размечены координаты в HTML разных
типов статей Wikipedia (горы, реки, сёла, острова), прежде чем писать парсер.

Не pytest-тест, делает реальные сетевые запросы.

Запуск (из папки backend, venv активен):
    python -m scripts.explore_coordinates
"""

from app.wikipedia.client import WikipediaClient

ARTICLES = {
    "гора": "https://en.wikipedia.org/wiki/Mount_Everest",
    "река": "https://en.wikipedia.org/wiki/Nile",
    "село": "https://en.wikipedia.org/wiki/Stow-on-the-Wold",
    "остров": "https://en.wikipedia.org/wiki/Isle_of_Skye",
}


def main() -> None:
    from bs4 import BeautifulSoup

    client = WikipediaClient()

    for object_type, url in ARTICLES.items():
        print("=" * 70)
        print(f"{object_type.upper()}: {url}")
        print("=" * 70)

        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        # Ищем всё, где в class встречается "geo" (geo-dec, geo, geo-nondefault и т.п.)
        geo_elements = soup.find_all(
            class_=lambda c: c and any("geo" in cls for cls in c)
        )

        if not geo_elements:
            print("  (элементов с classом geo* не найдено)")
        else:
            for el in geo_elements[:5]:
                print(f"  tag={el.name}, class={el.get('class')}")
                print(f"  text={el.get_text(strip=True)!r}")
                print(f"  html={str(el)[:200]}")
                print()

        # Отдельно проверим latitude/longitude, если geo-dec их не покрывает
        lat_el = soup.find(class_="latitude")
        lon_el = soup.find(class_="longitude")
        if lat_el or lon_el:
            print(f"  latitude span: {lat_el!r}")
            print(f"  longitude span: {lon_el!r}")

        print()


if __name__ == "__main__":
    main()