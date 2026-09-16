"""
Разведка: детальный разбор ссылки на geohack.toolforge.org — похоже, это
самый надёжный источник и десятичных координат, и названия точки.

Запуск:
    python -m scripts.explore_geohack_link
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

from app.wikipedia.client import WikipediaClient

ARTICLES = [
    "https://en.wikipedia.org/wiki/Mount_Everest",
    "https://en.wikipedia.org/wiki/Seven_Summits",
    "https://en.wikipedia.org/wiki/Isle_of_Skye",
]


def main() -> None:
    client = WikipediaClient()

    for url in ARTICLES:
        raw = client.fetch_article(url)
        soup = BeautifulSoup(raw.html, "html.parser")

        geohack_links = soup.find_all(
            "a", href=lambda h: h and "geohack.toolforge.org" in h
        )

        print(f"{raw.title}: найдено geohack-ссылок = {len(geohack_links)}")

        for link in geohack_links[:3]:
            href = link["href"]
            parsed = urlparse(href)
            params = parse_qs(parsed.query)

            print(f"  raw href: {href}")
            print(f"  pagename: {params.get('pagename')}")
            print(f"  params:   {params.get('params')}")
            print(f"  title:    {unquote(params.get('title', [''])[0])}")
            print()


if __name__ == "__main__":
    main()