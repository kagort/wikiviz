"""
Разведочный скрипт: изучает, как реально размечены числовые данные в HTML
статей Wikipedia (население, площадь, проценты) на английском и русском,
прежде чем писать NumberExtractor.

Запуск (из папки backend, venv активен):
    python -m scripts.explore_numbers
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

ARTICLES = {
    "страна (en)": "https://en.wikipedia.org/wiki/France",
    "страна (ru)": "https://ru.wikipedia.org/wiki/Франция",
    "город (en)": "https://en.wikipedia.org/wiki/Tokyo",
    "город (ru)": "https://ru.wikipedia.org/wiki/Токио",
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
        for row in rows[:40]:
            cells = row.find_all(["th", "td"])
            if len(cells) != 2:
                continue
            label_cell, data_cell = cells
            label_text = label_cell.get_text(strip=True)
            data_text = " ".join(data_cell.stripped_strings)

            # Интересуют строки, где data содержит цифру
            if any(ch.isdigit() for ch in data_text):
                print(f"  {label_text!r}: {data_text[:100]!r}")

        print()


if __name__ == "__main__":
    main()