"""
Диагностика: группируем найденные текстовые даты по заголовку раздела,
чтобы понять, не дают ли служебные разделы (References/Источники/
External links) непропорционально много ложных совпадений.

Запуск:
    python -m scripts.diagnose_text_dates_distribution
"""

from collections import Counter

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
        events = extract_text_dates(raw.html)

        counts = Counter(e.title for e in events)

        print(f"{raw.title}: всего {len(events)} дат")
        print("Распределение по разделам (топ-10):")
        for title, count in counts.most_common(10):
            print(f"  {count:4d}  {title!r}")
        print()


if __name__ == "__main__":
    main()