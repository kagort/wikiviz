"""
Ручной интеграционный скрипт: DateExtractor на широком наборе реальных
статей — современные даты (ISO) и BCE, разные типы объектов, en/ru.

Запуск (из папки backend, venv активен):
    python -m scripts.test_date_extractor
"""

from app.extractors.date_extractor import extract_dates
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    # Современные люди
    "https://en.wikipedia.org/wiki/Albert_Einstein",
    "https://ru.wikipedia.org/wiki/Эйнштейн,_Альберт",
    "https://en.wikipedia.org/wiki/Marie_Curie",
    "https://ru.wikipedia.org/wiki/Кюри,_Мария",

    # Античные люди (BCE)
    "https://en.wikipedia.org/wiki/Socrates",
    "https://ru.wikipedia.org/wiki/Сократ",
    "https://en.wikipedia.org/wiki/Julius_Caesar",
    "https://ru.wikipedia.org/wiki/Юлий_Цезарь",
    "https://en.wikipedia.org/wiki/Aristotle",

    # Организации
    "https://en.wikipedia.org/wiki/United_Nations",
    "https://ru.wikipedia.org/wiki/Организация_Объединённых_Наций",
    "https://en.wikipedia.org/wiki/NASA",

    # Фильмы
    "https://en.wikipedia.org/wiki/Inception",
    "https://ru.wikipedia.org/wiki/Начало_(фильм)",

    # Исторические события (BCE)
    "https://en.wikipedia.org/wiki/Battle_of_Actium",
    "https://en.wikipedia.org/wiki/Founding_of_Rome",

    # Страны (дата основания/независимости)
    "https://en.wikipedia.org/wiki/United_States",
    "https://ru.wikipedia.org/wiki/Россия",
]


def main() -> None:
    client = WikipediaClient()

    total_events = 0
    articles_without_dates = []

    for url in ARTICLES:
        try:
            raw = client.fetch_article(url)
        except Exception as exc:
            print(f"ОШИБКА при получении {url}: {exc}")
            print()
            continue

        events = extract_dates(raw.html)
        total_events += len(events)

        print(f"{raw.title}: найдено дат = {len(events)}")
        for event in events:
            print(f"  [{event.id}] {event.title!r}: date={event.date}, precision={event.date_precision.value}")

        if not events:
            articles_without_dates.append(raw.title)

        print()

    print("=" * 60)
    print(f"ИТОГО: {total_events} дат по {len(ARTICLES)} статьям")
    if articles_without_dates:
        print(f"Статьи без единой найденной даты: {articles_without_dates}")


if __name__ == "__main__":
    main()