
from app.wikipedia.content_models import ArticleSection
from app.wikipedia.html_extractor import extract_sections


def test_extract_h2_section():
    html = """
    <h2>History</h2>
    <p>Python was created by Guido van Rossum.</p>
    <p>The first version was released in 1991.</p>

    <h2>Design</h2>
    <p>Python emphasizes readability.</p>
    """

    sections = extract_sections(html)

    assert sections == [
        ArticleSection(
            level=2,
            title="History",
            html=(
                "<p>Python was created by Guido van Rossum.</p>"
                "<p>The first version was released in 1991.</p>"
            ),
        ),
        ArticleSection(
            level=2,
            title="Design",
            html="<p>Python emphasizes readability.</p>",
        ),
    ]


def test_extract_h2_and_h3_sections():
    html = """
    <h2>Design</h2>
    <p>Python has a clear syntax.</p>

    <h3>Syntax</h3>
    <p>The syntax is readable.</p>

    <h3>Indentation</h3>
    <p>Indentation defines code blocks.</p>

    <h2>Features</h2>
    <p>Python has many features.</p>
    """

    sections = extract_sections(html)

    assert sections == [
        ArticleSection(
            level=2,
            title="Design",
            html="<p>Python has a clear syntax.</p>",
        ),
        ArticleSection(
            level=3,
            title="Syntax",
            html="<p>The syntax is readable.</p>",
        ),
        ArticleSection(
            level=3,
            title="Indentation",
            html="<p>Indentation defines code blocks.</p>",
        ),
        ArticleSection(
            level=2,
            title="Features",
            html="<p>Python has many features.</p>",
        ),
    ]


def test_nested_content_belongs_to_section():
    html = """
    <h2>Design</h2>
    <p>Main section text.</p>

    <h3>Syntax</h3>
    <p>Syntax details.</p>

    <h2>Features</h2>
    <p>Feature details.</p>
    """

    sections = extract_sections(html)

    assert sections[0].title == "Design"
    assert sections[0].html == "<p>Main section text.</p>"

    assert sections[1].title == "Syntax"
    assert sections[1].html == "<p>Syntax details.</p>"

    assert sections[2].title == "Features"
    assert sections[2].html == "<p>Feature details.</p>"


def test_section_preserves_inner_html():
    html = """
    <h2>Example</h2>
    <p>This is <b>important</b> text.</p>
    <ul>
        <li>First item</li>
        <li>Second item</li>
    </ul>
    """

    sections = extract_sections(html)

    assert len(sections) == 1
    assert sections[0].title == "Example"
    assert "<b>important</b>" in sections[0].html
    assert "<ul>" in sections[0].html
    assert "<li>First item</li>" in sections[0].html


def test_ignore_content_before_first_heading():
    html = """
    <p>Lead paragraph.</p>

    <h2>History</h2>
    <p>History text.</p>
    """

    sections = extract_sections(html)

    assert sections == [
        ArticleSection(
            level=2,
            title="History",
            html="<p>History text.</p>",
        )
    ]


def test_empty_html_returns_empty_list():
    assert extract_sections("") == []


def test_html_without_headings_returns_empty_list():
    html = """
    <p>Just a paragraph.</p>
    <p>No headings here.</p>
    """

    assert extract_sections(html) == []


def test_extract_sections_from_mediawiki_heading_wrapper():
    html = """
    <div class="mw-heading mw-heading2">
        <h2 id="History">History</h2>
        <span class="mw-editsection">
            [edit]
        </span>
    </div>

    <p>Python was created by Guido van Rossum.</p>
    <p>The first version was released in 1991.</p>

    <div class="mw-heading mw-heading2">
        <h2 id="Design">Design</h2>
        <span class="mw-editsection">
            [edit]
        </span>
    </div>

    <p>Python emphasizes readability.</p>
    """

    sections = extract_sections(html)

    assert sections == [
        ArticleSection(
            level=2,
            title="History",
            html=(
                "<p>Python was created by Guido van Rossum.</p>"
                "<p>The first version was released in 1991.</p>"
            ),
        ),
        ArticleSection(
            level=2,
            title="Design",
            html="<p>Python emphasizes readability.</p>",
        ),
    ]
def test_extract_sections_from_mediawiki_heading_wrapper():
    html = """
    <div class="mw-heading mw-heading2">
        <h2 id="History">History</h2>
        <span class="mw-editsection">
            [edit]
        </span>
    </div>

    <p>Python was created by Guido van Rossum.</p>
    <p>The first version was released in 1991.</p>

    <div class="mw-heading mw-heading2">
        <h2 id="Design">Design</h2>
        <span class="mw-editsection">
            [edit]
        </span>
    </div>

    <p>Python emphasizes readability.</p>
    """

    sections = extract_sections(html)

    assert sections == [
        ArticleSection(
            level=2,
            title="History",
            html=(
                "<p>Python was created by Guido van Rossum.</p>"
                "<p>The first version was released in 1991.</p>"
            ),
        ),
        ArticleSection(
            level=2,
            title="Design",
            html="<p>Python emphasizes readability.</p>",
        ),
    ]
