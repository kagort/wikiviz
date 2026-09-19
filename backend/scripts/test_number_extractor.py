"""
Ручной интеграционный скрипт: NumberExtractor на реальных статьях
(страна и город, en+ru) - тех же, что использовались при разведке.

Запуск (из папки backend, venv активен):
    python -m scripts.test_number_extractor
"""

from app.extractors.number_extractor import extract_numbers
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    ("https://en.wikipedia.org/wiki/France", "en"),
    ("https://ru.wikipedia.org/wiki/Франция", "ru"),
    ("https://en.wikipedia.org/wiki/Tokyo", "en"),
    ("https://ru.wikipedia.org/wiki/Токио", "ru"),
]


def main() -> None:
    client = WikipediaClient()

    for url, language in ARTICLES:
        raw = client.fetch_article(url)
        numbers = extract_numbers(raw.html, language=language)

        print(f"{raw.title} ({language}): найдено чисел = {len(numbers)}")
        for n in numbers[:20]:
            print(f"  {n.label!r}: value={n.value}, unit={n.unit!r}")
        print()


if __name__ == "__main__":
    main()