"""
Ручной интеграционный скрипт: полная цепочка URL -> NormalizedArticleModel
на реальной статье Wikipedia. Не pytest-тест — делает настоящий сетевой запрос.

Запуск (из папки backend, venv активен):
    python -m scripts.test_article_normalizer
"""

from app.extractors.article_normalizer import normalize_article
from app.wikipedia.client import WikipediaClient


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )

    result = normalize_article(raw)

    print(f"article.id: {result.article.id}")
    print(f"article.title: {result.article.title}")
    print(f"article.language: {result.article.language}")
    print(f"article.url: {result.article.url}")
    print(f"top-level sections: {len(result.sections)}")
    print()

    for section in result.sections[:5]:
        print(f"[h{section.level}] {section.title}  ({len(section.children)} children)")
        for child in section.children[:3]:
            print(f"  [h{child.level}] {child.title}")

    print()
    print("--- Полный JSON (первые 2000 символов) ---")
    print(result.model_dump_json(indent=2)[:2000])


if __name__ == "__main__":
    main()