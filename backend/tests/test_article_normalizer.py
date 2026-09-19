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


def test_normalize_article_fills_tables():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="""
        <table class="wikitable">
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        """,
    )

    result = normalize_article(raw)

    assert len(result.tables) == 1
    assert result.tables[0].columns == ["A", "B"]


def test_normalize_article_fills_locations():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="""
        <span class="latitude">27°59′18″N</span>
        <span class="longitude">86°55′31″E</span>
        """,
    )

    result = normalize_article(raw)

    assert len(result.locations) == 1
    assert result.locations[0].name == "Test"


def test_normalize_article_fills_images():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="""
        <div class="thumb">
            <a href="/wiki/File:Example.jpg" class="mw-file-description">
                <img src="//upload.wikimedia.org/thumb/e/330px-Example.jpg" />
            </a>
            <div class="thumbcaption">A caption</div>
        </div>
        """,
    )

    result = normalize_article(raw)

    assert len(result.images) == 1
    assert result.images[0].caption == "A caption"


def test_normalize_article_fills_events_from_both_sources():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="""
        <table class="infobox">
            <tr><td class="infobox-label">Born</td><td class="infobox-data">(1879-03-14)</td></tr>
        </table>
        <h2>History</h2>
        <p>Signed on 26 June 1945.</p>
        """,
    )

    result = normalize_article(raw)

    assert len(result.events) == 2
    sources = {e.source.value for e in result.events}
    assert "infobox" in sources
    assert "article_text" in sources


def test_normalize_article_fills_numbers():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="""
        <table class="infobox">
            <tr><td class="infobox-label">Population</td><td class="infobox-data">69,081,996</td></tr>
        </table>
        """,
    )

    result = normalize_article(raw)

    assert len(result.numbers) == 1
    assert result.numbers[0].value == 69081996.0


def test_normalize_article_remaining_fields_are_still_stubs():
    raw = RawArticle(
        page_id=1, title="Test", language="en", url="https://en.wikipedia.org/wiki/Test",
        html="<p>Text.</p>",
    )

    result = normalize_article(raw)

    assert result.infobox == {}
    assert result.people == []
    assert result.organizations == []
    assert result.works == []
    assert result.relations == []
    assert result.links == []
    assert result.metadata == {}
