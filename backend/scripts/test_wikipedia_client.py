from app.wikipedia.client import WikipediaClient


URL = "https://en.wikipedia.org/wiki/Python_(programming_language)"


def main() -> None:
    client = WikipediaClient()

    article = client.fetch_article(URL)

    print(f"title: {article.title}")
    print(f"page_id: {article.page_id}")
    print(f"language: {article.language}")
    print(f"revision_id: {article.revision_id}")
    print(f"html length: {len(article.html)}")
    print(f"url: {article.url}")


if __name__ == "__main__":
    main()