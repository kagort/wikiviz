"""
Дополнительная разведка BCE-дат: ищем infobox с датами до нашей эры (не
только в тексте статьи, как было с Battle of Actium), и проверяем разные
нотации (BC/BCE, "circa"/"c.", наличие ISO с отрицательным годом).

Запуск:
    python -m scripts.explore_dates_bce
"""

import re

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ISO_DATE_RE = re.compile(r"\((-?\d{1,4})-(\d{2})-(\d{2})\)")

ARTICLES = {
    "историческая личность (Julius Caesar)": "https://en.wikipedia.org/wiki/Julius_Caesar",
    "древний город (Rome founding)": "https://en.wikipedia.org/wiki/Founding_of_Rome",
    "философ (Socrates)": "https://en.wikipedia.org/wiki/Socrates",
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
            if "born" not in label_text.lower() and "died" not in label_text.lower():
                continue

            raw_text = data_cell.get_text()
            iso_match = ISO_DATE_RE.search(raw_text)

            print(f"  label={label_text!r}")
            print(f"  visible text: {data_cell.get_text(strip=True)[:120]!r}")
            print(f"  ISO regex match: {iso_match.group(0) if iso_match else None}")
            print()

        # Также ищем "BC"/"BCE"/"c." прямо в тексте, если infobox не дал результата
        full_text = soup.get_text()
        for marker in ["BC)", "BCE)", "BC.", "BCE.", " BC ", " BCE "]:
            idx = full_text.find(marker)
            if idx != -1:
                print(f"  найден маркер {marker!r}: ...{full_text[max(0, idx-60):idx+10]}...")
                break
        print()


if __name__ == "__main__":
    main()