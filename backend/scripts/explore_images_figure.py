"""
Уточняющая разведка: точная структура обёртки вокруг ГЛАВНОГО изображения
статьи (не иконки) — ищем <figure>, figcaption, и реальный родительский
контейнер.

Запуск:
    python -m scripts.explore_images_figure
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

URL = "https://en.wikipedia.org/wiki/Mount_Everest"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    # Первое изображение с разумным размером (не иконка) — по разведке это
    # фото горы, ~288x192.
    images = soup.find_all("img")
    real_images = [
        img for img in images
        if img.get("width") and int(img["width"]) >= 100
    ]

    print(f"Изображений с width >= 100: {len(real_images)}")
    print()

    for img in real_images[:3]:
        print(f"src: {img.get('src')}")
        print(f"width: {img.get('width')}")

        # Поднимаемся по родителям, печатаем каждый уровень
        parent = img.parent
        for level in range(5):
            if parent is None:
                break
            print(f"  parent[{level}]: <{parent.name} class={parent.get('class')} typeof={parent.get('typeof')}>")
            parent = parent.parent

        # Ищем figcaption где-то рядом (в общем предке figure)
        figure = img.find_parent("figure")
        if figure:
            figcaption = figure.find("figcaption")
            print(f"  figcaption: {figcaption.get_text(strip=True) if figcaption else None!r}")
        else:
            print("  <figure> не найден вообще")
        print()


if __name__ == "__main__":
    main()