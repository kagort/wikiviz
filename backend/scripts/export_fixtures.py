"""
Ручной интеграционный скрипт: выгружает реальные статьи Wikipedia
в NormalizedArticleModel и сохраняет как JSON-фикстуры для frontend-тестов.

Запуск: python -m scripts.export_fixtures
"""
import json
from pathlib import Path

from app.wikipedia.client import WikipediaClient
from app.extractors.article_normalizer import normalize_article

# Статьи для выгрузки: (URL, имя выходного файла)
ARTICLES = [
    ("https://en.wikipedia.org/wiki/Python_(programming_language)", "python.json"),
    ("https://en.wikipedia.org/wiki/France", "france.json"),
    ("https://ru.wikipedia.org/wiki/Токио", "tokyo-ru.json"),
]

OUTPUT_DIR = Path(__file__).parent.parent.parent / "frontend" / "tests" / "fixtures" / "real"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = WikipediaClient()

    for url, filename in ARTICLES:
        print(f"Fetching {url} ...")
        raw = client.fetch_article(url)
        normalized = normalize_article(raw)

        output_path = OUTPUT_DIR / filename
        output_path.write_text(
            normalized.model_dump_json(indent=2),
            encoding="utf-8",
        )
        print(f"  -> saved to {output_path} "
              f"(sections={len(normalized.sections)}, "
              f"tables={len(normalized.tables)}, "
              f"locations={len(normalized.locations)}, "
              f"images={len(normalized.images)}, "
              f"events={len(normalized.events)}, "
              f"numbers={len(normalized.numbers)})")

    print("\nDone.")


if __name__ == "__main__":
    main()