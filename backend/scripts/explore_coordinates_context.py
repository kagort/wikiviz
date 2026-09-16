"""
Продолжение разведки: контекст вокруг координат и проверка на множественные
координаты в одной статье.

Запуск:
    python -m scripts.explore_coordinates_context
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

# Остров с несколькими примечательными точками — кандидат на проверку "несколько координат"
URL = "https://en.wikipedia.org/wiki/Isle_of_Skye"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    lat_spans = soup.find_all(class_="latitude")
    lon_spans = soup.find_all(class_="longitude")

    print(f"Найдено latitude spans: {len(lat_spans)}")
    print(f"Найдено longitude spans: {len(lon_spans)}")
    print()

    for i, lat in enumerate(lat_spans[:3]):
        print(f"--- Координата #{i} ---")
        print(f"latitude text: {lat.get_text(strip=True)!r}")

        # Поднимаемся на несколько уровней вверх, смотрим на родителя
        parent = lat.parent
        for level in range(4):
            if parent is None:
                break
            print(f"  parent[{level}]: <{parent.name} class={parent.get('class')}>")
            parent = parent.parent

        # Полный HTML ближайшего осмысленного контейнера (например, span.geo-inline или span#coordinates)
        container = lat.find_parent(["span", "div"], class_=["geo-inline", "vcard", "infobox"])
        if container:
            print(f"  ближайший контейнер: <{container.name} class={container.get('class')}>")
        print()


if __name__ == "__main__":
    main()