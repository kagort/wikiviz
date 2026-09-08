from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient


def main() -> None:
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

    article = WikipediaClient().fetch_article(url)
    soup = BeautifulSoup(article.html, "html.parser")

    heading = soup.find("h2")

    print("HEADING:")
    print(heading)
    print()

    print("PARENT:")
    print(heading.parent)
    print()

    print("PARENT CHILDREN:")
    for child in heading.parent.children:
        print("CHILD:", repr(str(child)[:300]))
        print()

    print("NEXT SIBLINGS:")
    for sibling in heading.next_siblings:
        print(repr(str(sibling)[:300]))


if __name__ == "__main__":
    main()