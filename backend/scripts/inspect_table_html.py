"""
Разведочный скрипт: смотрит на сырую HTML-разметку таблицы населения
Токио, чтобы подтвердить гипотезу о скрытых sort-key spans перед
исправлением table_extractor.py.

Запуск: python -m scripts.inspect_table_html
"""
from collections import Counter

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

URL = "https://ru.wikipedia.org/wiki/Токио"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    tables = soup.find_all("table", class_="wikitable")
    print(f"Найдено wikitable: {len(tables)}")

    # Таблица населения — вторая (index 1), по данным прошлой выгрузки
    population_table = tables[1]

    # Берём первую строку данных (после заголовка) для разбора
    all_rows = population_table.find_all("tr")
    data_row = all_rows[2]  # строка "1 октября 1920"
    cells = data_row.find_all(["td", "th"])

    print(f"\nЯчеек в строке: {len(cells)}")
    print("\n--- Сырой HTML второй ячейки (население) ---")
    print(cells[1].prettify())

    # Считаем, какие теги/классы/стили встречаются внутри ячеек таблицы —
    # группировка находок перед исправлением
    tag_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    for cell in population_table.find_all(["td", "th"]):
        for tag in cell.find_all(True):
            tag_counter[tag.name] += 1
            style = tag.get("style")
            if style:
                style_counter[style] += 1

    print("\n--- Вложенные теги внутри ячеек (счётчик) ---")
    for tag, count in tag_counter.most_common():
        print(f"  {tag}: {count}")

    print("\n--- Встреченные значения style= (счётчик) ---")
    for style, count in style_counter.most_common():
        print(f"  {style!r}: {count}")


if __name__ == "__main__":
    main()