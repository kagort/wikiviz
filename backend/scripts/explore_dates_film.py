"""
Финальная проверка гипотезы: ISO-дата в скобках (YYYY-MM-DD) как надёжный
паттерн, не привязанный к конкретному CSS-классу.

Запуск:
    python -m scripts.explore_dates_film
"""

import re

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ISO_DATE_RE = re.compile(r"\((\d{4})-(\d{2})-(\d{2})\)")

URL = "https://en.wikipedia.org/wiki/Inception"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    rows = soup.find_all("tr")
    for row in rows[:20]:
        label_cell = row.find(class_="infobox-label")
        data_cell = row.find(class_="infobox-data")
        if not label_cell or not data_cell:
            continue

        raw_text = data_cell.get_text()  # без strip, чтобы видеть всё как есть
        match = ISO_DATE_RE.search(raw_text)

        label_text = label_cell.get_text(strip=True)
        print(f"label={label_text!r}")
        if match:
            print(f"  ISO найден через общий regex: {match.group(0)}")
        else:
            print(f"  ISO не найден, raw data text: {raw_text[:100]!r}")
        print()


if __name__ == "__main__":
    main()