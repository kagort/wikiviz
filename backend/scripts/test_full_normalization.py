"""
Финальная интеграционная проверка Phase 4: полная цепочка
URL -> WikipediaClient -> RawArticle -> normalize_article() ->
NormalizedArticleModel со ВСЕМИ заполненными extractors одновременно.

Запуск (из папки backend, venv активен):
    python -m scripts.test_full_normalization
"""

from app.extractors.article_normalizer import normalize_article
from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://en.wikipedia.org/wiki/France",
    "https://ru.wikipedia.org/wiki/Токио",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)
        result = normalize_article(raw)

        print(f"=== {result.article.title} ===")
        print(f"  sections:  {len(result.sections)} (top-level)")
        print(f"  tables:    {len(result.tables)}")
        print(f"  locations: {len(result.locations)}")
        print(f"  images:    {len(result.images)}")
        print(f"  events:    {len(result.events)}")
        print(f"  numbers:   {len(result.numbers)}")
        print()

    # Дополнительно: печатаем полный JSON первой статьи (обрезанный),
    # чтобы своими глазами увидеть итоговую структуру контракта.
    raw = client.fetch_article(ARTICLES[0])
    result = normalize_article(raw)
    print("--- Полный JSON первой статьи (первые 3000 символов) ---")
    print(result.model_dump_json(indent=2)[:3000])


if __name__ == "__main__":
    main()