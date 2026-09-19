"""
Проверка: размечает ли MediaWiki заголовки групп (Area/Population/...)
отдельным CSS-классом, отличным от заголовка статьи и подписей к
изображениям/картам - чтобы не полагаться на эвристики по длине текста.

Запуск:
    python -m scripts.explore_numbers_group_classes
"""

from app.wikipedia.client import WikipediaClient
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/France"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    infobox = soup.find("table", class_="infobox")
    rows = infobox.find_all("tr")

    for row in rows[:35]:
        cells = row.find_all(["th", "td"])
        if len(cells) != 1:
            continue
        cell = cells[0]
        text = cell.get_text(" ", strip=True)[:50]
        print(f"tag={cell.name}  class={cell.get('class')}  text={text!r}")


if __name__ == "__main__":
    main()