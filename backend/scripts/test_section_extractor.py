"""
Ручной интеграционный скрипт: проверяет extract_sections() на реальной статье Wikipedia.

Это НЕ pytest-тест — pytest автоматически собирает только функции с именем test_*
в файлах внутри tests/, а не в scripts/, но имя файла намеренно похоже на тестовое
для наглядности связи с tests/test_section_extractor.py. Здесь мы сознательно
делаем реальный сетевой запрос, чего автоматические тесты делать не должны.

Запуск (из папки backend, venv активен):
    python -m scripts.test_section_extractor
"""

from app.extractors.section_extractor import extract_sections
from app.wikipedia.client import WikipediaClient


def main() -> None:
    client = WikipediaClient()
    article = client.fetch_article(
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )

    sections = extract_sections(article.html)

    print(f"title: {article.title}")
    print(f"language: {article.language}")
    print(f"sections: {len(sections)}")
    print()

    for section in sections[:5]:
        indent = "  " * (section.level - 2)
        print(f"{indent}[h{section.level}] {section.title}")


if __name__ == "__main__":
    main()