"""
Разведочный скрипт: изучает, как реально размечены изображения в HTML статей
Wikipedia (infobox-изображение и статья с несколькими изображениями),
прежде чем писать ImageExtractor.

Запуск (из папки backend, venv активен):
    python -m scripts.explore_images
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ARTICLES = {
    "infobox-изображение": "https://en.wikipedia.org/wiki/Mount_Everest",
    "несколько изображений": "https://en.wikipedia.org/wiki/Python_(programming_language)",
}


def main() -> None:
    client = WikipediaClient()

    for label, url in ARTICLES.items():
        print("=" * 70)
        print(f"{label.upper()}: {url}")
        print("=" * 70)

        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        images = soup.find_all("img")
        print(f"Всего <img> тегов: {len(images)}")
        print()

        for img in images[:5]:
            print(f"  src: {img.get('src')}")
            print(f"  srcset: {(img.get('srcset') or '')[:100]}")
            print(f"  alt: {img.get('alt')!r}")
            print(f"  class: {img.get('class')}")
            print(f"  width/height: {img.get('width')}/{img.get('height')}")

            # Ищем ближайший <figure> или элемент с caption рядом
            figure = img.find_parent(["figure", "div"], class_=lambda c: c and "thumb" in c)
            if figure:
                caption = figure.find(class_=lambda c: c and "caption" in c)
                print(f"  найден thumb/figure, caption: {caption.get_text(strip=True) if caption else None!r}")
            else:
                print(f"  thumb/figure контейнер не найден")
            print()


if __name__ == "__main__":
    main()