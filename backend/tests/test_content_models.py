from app.wikipedia.content_models import ArticleSection, ParsedArticle


def test_article_section():
    section = ArticleSection(
        level=1,
        title="History",
        html="<p>Python was created by Guido van Rossum.</p>",
    )

    assert section.level == 1
    assert section.title == "History"
    assert section.html == "<p>Python was created by Guido van Rossum.</p>"


def test_parsed_article():
    section = ArticleSection(
        level=1,
        title="History",
        html="<p>Python was created by Guido van Rossum.</p>",
    )

    article = ParsedArticle(
        title="Python (programming language)",
        language="en",
        url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        sections=[section],
    )

    assert article.title == "Python (programming language)"
    assert article.language == "en"
    assert article.url == (
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )
    assert len(article.sections) == 1
    assert article.sections[0].title == "History"


def test_parsed_article_can_have_multiple_sections():
    article = ParsedArticle(
        title="Test",
        language="en",
        url="https://en.wikipedia.org/wiki/Test",
        sections=[
            ArticleSection(
                level=1,
                title="History",
                html="<p>History.</p>",
            ),
            ArticleSection(
                level=1,
                title="Features",
                html="<p>Features.</p>",
            ),
            ArticleSection(
                level=2,
                title="Syntax",
                html="<p>Syntax.</p>",
            ),
        ],
    )

    assert len(article.sections) == 3
    assert article.sections[0].level == 1
    assert article.sections[1].level == 1
    assert article.sections[2].level == 2
    assert article.sections[2].title == "Syntax"