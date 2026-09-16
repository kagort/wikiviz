"""
Разведочный скрипт: изучает, как реально размечены даты в HTML статей
Wikipedia — в infobox (Born/Died/Founded) и в датах до нашей эры (BCE),
прежде чем писать DateExtractor.

Запуск (из папки backend, venv активен):
    python -m scripts.explore_dates
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ARTICLES = {
    "человек (born/died)": "https://en.wikipedia.org/wiki/Albert_Einstein",
    "организация (founded)": "https://en.wikipedia.org/wiki/United_Nations",
    "историческое событие BCE": "https://en.wikipedia.org/wiki/Battle_of_Actium",
}


def main() -> None:
    client = WikipediaClient()

    for label, url in ARTICLES.items():
        print("=" * 70)
        print(f"{label.upper()}: {url}")
        print("=" * 70)

        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        # Ищем строки infobox, где label похож на дату
        date_keywords = ["born", "died", "founded", "date", "established"]
        rows = soup.find_all("tr")

        found_any = False
        for row in rows:
            label_cell = row.find(class_="infobox-label")
            if not label_cell:
                continue
            label_text = label_cell.get_text(strip=True).lower()
            if any(kw in label_text for kw in date_keywords):
                found_any = True
                data_cell = row.find(class_="infobox-data")
                print(f"  label: {label_cell.get_text(strip=True)!r}")
                if data_cell:
                    print(f"  data text: {data_cell.get_text(strip=True)!r}")
                    print(f"  data html (первые 300): {str(data_cell)[:300]}")
                print()

        if not found_any:
            print("  (строк infobox с датой не найдено)")

        # Отдельно: microformat <span class="bday"> (часто используется для дат рождения)
        bday = soup.find(class_="bday")
        print(f"  span.bday: {bday.get_text(strip=True) if bday else None!r}")
        print()


if __name__ == "__main__":
    main()