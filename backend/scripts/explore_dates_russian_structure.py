"""
Разведка структуры infobox в русской Wikipedia — CSS-классы могут
отличаться от английской версии. Также проверяем, почему статья
про Эйнштейна не дала результата вовсе.

Запуск:
    python -m scripts.explore_dates_russian_structure
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient


def dump_infobox(url: str, label: str) -> None:
    print("=" * 70)
    print(f"{label}: {url}")
    print("=" * 70)

    client = WikipediaClient()
    raw = client.fetch_article(url)

    print(f"page_id={raw.page_id}, title={raw.title!r}, html length={len(raw.html)}")

    soup = BeautifulSoup(raw.html, "html.parser")
    infobox = soup.find("table", class_="infobox")

    if infobox is None:
        print("  <table class='infobox'> НЕ НАЙДЕН вообще")
        # Проверим, есть ли вообще какие-то таблицы
        all_tables = soup.find_all("table")
        print(f"  Всего <table> на странице: {len(all_tables)}")
        for t in all_tables[:3]:
            print(f"    class={t.get('class')}")
        return

    # Печатаем первые несколько строк целиком с их классами
    rows = infobox.find_all("tr")
    print(f"  Найдено строк в infobox: {len(rows)}")
    for row in rows[:10]:
        cells = row.find_all(["th", "td"])
        for cell in cells:
            print(f"    <{cell.name} class={cell.get('class')}> {cell.get_text(strip=True)[:60]!r}")
        print()


if __name__ == "__main__":
    dump_infobox("https://ru.wikipedia.org/wiki/Сократ", "СОКРАТ")
    dump_infobox("https://ru.wikipedia.org/wiki/Эйнштейн,_Альберт", "ЭЙНШТЕЙН")