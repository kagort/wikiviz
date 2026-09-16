"""
Разведка BCE/дат в русскоязычной Wikipedia — проверяем обозначения эпох
(до н. э., н. э.) и формат ISO/микроформатов, которые могут отличаться
от английской версии.

Запуск:
    python -m scripts.explore_dates_russian
"""

import re

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ISO_DATE_RE = re.compile(r"\((\d{4})-(\d{2})-(\d{2})\)")

ARTICLES = {
    "историческая личность (Юлий Цезарь)": "https://ru.wikipedia.org/wiki/Юлий_Цезарь",
    "философ (Сократ)": "https://ru.wikipedia.org/wiki/Сократ",
    "современный человек (Эйнштейн)": "https://ru.wikipedia.org/wiki/Эйнштейн,_Альберт",
}


def main() -> None:
    client = WikipediaClient()

    for label, url in ARTICLES.items():
        print("=" * 70)
        print(f"{label.upper()}: {url}")
        print("=" * 70)

        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        rows = soup.find_all("tr")
        for row in rows[:20]:
            label_cell = row.find(class_="infobox-label")
            data_cell = row.find(class_="infobox-data")
            if not label_cell or not data_cell:
                continue

            label_text = label_cell.get_text(strip=True)
            if "род" not in label_text.lower() and "умер" not in label_text.lower() and "смерт" not in label_text.lower():
                continue

            raw_text = data_cell.get_text()
            visible_text = " ".join(data_cell.stripped_strings)
            iso_match = ISO_DATE_RE.search(raw_text)

            print(f"  label={label_text!r}")
            print(f"  visible text: {visible_text[:150]!r}")
            print(f"  ISO regex match: {iso_match.group(0) if iso_match else None}")
            print()

        # Ищем маркеры эпохи прямо в тексте статьи
        full_text = soup.get_text()
        for marker in ["до н. э.", "до н.э.", "н. э.", "до Р. Х.", "до Р.Х."]:
            idx = full_text.find(marker)
            if idx != -1:
                print(f"  найден маркер {marker!r}: ...{full_text[max(0, idx-50):idx+20]}...")
        print()


if __name__ == "__main__":
    main()