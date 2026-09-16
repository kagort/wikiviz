"""
Ручной интеграционный скрипт: TableExtractor на реальной статье Wikipedia.
Не pytest-тест — делает настоящий сетевой запрос.

Запуск (из папки backend, venv активен):
    python -m scripts.test_table_extractor
"""

from app.extractors.table_extractor import extract_tables
from app.wikipedia.client import WikipediaClient


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )

    tables = extract_tables(raw.html)

    print(f"article: {raw.title}")
    print(f"tables found: {len(tables)}")
    print()

    for table in tables:
        print(f"[{table.id}] title={table.title!r}")
        print(f"  columns: {table.columns}")
        print(f"  rows: {len(table.rows)}")
        if table.rows:
            print(f"  first row: {table.rows[0]}")
        print()


if __name__ == "__main__":
    main()