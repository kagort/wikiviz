"""
Ручной интеграционный скрипт: TextDateExtractor на реальных статьях,
включая тот случай (ООН), который выявил необходимость извлечения дат
из обычного текста, а не только из infobox.

Запуск (из папки backend, venv активен):
    python -m scripts.test_text_date_extractor
"""

from app.extractors.date_extractor import extract_dates
from app.extractors.text_date_extractor import extract_text_dates
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://ru.wikipedia.org/wiki/Организация_Объединённых_Наций",
    "https://en.wikipedia.org/wiki/United_Nations",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)

        infobox_events = extract_dates(raw.html)
        text_events = extract_text_dates(raw.html)

        print(f"{raw.title}")
        print(f"  из infobox: {len(infobox_events)}")
        for e in infobox_events:
            print(f"    [{e.id}] {e.title!r}: {e.date} (precision={e.date_precision.value})")

        print(f"  из текста: {len(text_events)}")
        for e in text_events[:10]:
            print(f"    [{e.id}] {e.title!r}: {e.date} (confidence={e.confidence})")
        print()


if __name__ == "__main__":
    main()