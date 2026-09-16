"""
Ручной интеграционный скрипт: ImageExtractor на реальных статьях.

Запуск (из папки backend, venv активен):
    python -m scripts.test_image_extractor
"""

from app.extractors.image_extractor import extract_images
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://en.wikipedia.org/wiki/Mount_Everest",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)
        images = extract_images(raw.html)

        print(f"{raw.title}: найдено изображений = {len(images)}")
        for img in images[:5]:
            print(f"  caption: {img.caption!r}")
            print(f"  alt: {img.alt!r}")
            print(f"  url: {img.url}")
            print()
        print()


if __name__ == "__main__":
    main()