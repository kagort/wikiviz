from app.wikipedia.client import WikipediaClient
from app.wikipedia.html_extractor import extract_sections


def main() -> None:
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

    client = WikipediaClient()

    article = client.fetch_article(url)
    sections = extract_sections(article.html)

    print(f"title: {article.title}")
    print(f"language: {article.language}")
    print(f"sections: {len(sections)}")
    print()

    for section in sections[:5]:
        print(f"[h{section.level}] {section.title}")
        print(f"HTML length: {len(section.html)}")
        print(section.html[:1000])
        print("-" * 80)


if __name__ == "__main__":
    main()