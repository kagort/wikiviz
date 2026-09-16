from app.extractors.article_normalizer import normalize_article
from app.wikipedia.models import RawArticle


def test_normalize_article_basic_fields():
    raw = RawArticle(
        page_id=42,
        title="Test Article",
        language="en",
        url="https://en.wikipedia.org/wiki/Test_Article",
        html="<h2>History</h2><p>Some text.</p>",
        revision_id=12345,
    )

    result = normalize_article(raw)

    assert result.article.id == 42
    assert result.article.title == "Test Article"
    assert result.article.language == "en"
    assert result.article.url == "https://en.wikipedia.org/wiki/Test_Article"


def test_normalize_article_builds_section_tree():
    raw = RawArticle(
        page_id=1,
        title="Test",
        language="en",
        url="https://en.wikipedia.org/wiki/Test",
        html="""
        <h2>Design</h2>
        <p>...</p>
        <h3>Syntax</h3>
        <p>...</p>
        <h2>Features</h2>
        <p>...</p>
        """,
    )

    result = normalize_article(raw)

    assert len(result.sections) == 2
    assert result.sections[0].title == "Design"
    assert result.sections[0].children[0].title == "Syntax"
    assert result.sections[1].title == "Features"


def test_normalize_article_with_no_sections():
    raw = RawArticle(
        page_id=1,
        title="Test",
        language="en",
        url="https://en.wikipedia.org/wiki/Test",
        html="<p>Just a paragraph, no headings.</p>",
    )

    result = normalize_article(raw)

    assert result.sections == []


def test_normalize_article_other_fields_are_empty_stubs():
    raw = RawArticle(
        page_id=1,
        title="Test",
        language="en",
        url="https://en.wikipedia.org/wiki/Test",
        html="<p>Text.</p>",
    )

    result = normalize_article(raw)

    assert result.infobox == {}
    assert result.tables == []
    assert result.locations == []
    assert result.events == []
    assert result.numbers == []
    assert result.people == []
    assert result.organizations == []
    assert result.works == []
    assert result.images == []