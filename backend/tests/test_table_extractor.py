from app.extractors.table_extractor import extract_tables


def test_extract_simple_table():
    html = """
    <table class="wikitable">
        <caption>Population</caption>
        <tr><th>Year</th><th>Population</th></tr>
        <tr><td>2000</td><td>100000</td></tr>
        <tr><td>2010</td><td>120000</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert len(tables) == 1
    assert tables[0].title == "Population"
    assert tables[0].columns == ["Year", "Population"]
    assert tables[0].rows == [["2000", "100000"], ["2010", "120000"]]


def test_table_without_caption_has_none_title():
    html = """
    <table class="wikitable">
        <tr><th>A</th><th>B</th></tr>
        <tr><td>1</td><td>2</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].title is None


def test_ignores_non_wikitable_tables():
    html = """
    <table class="infobox">
        <tr><td>Should be ignored</td></tr>
    </table>
    <table class="wikitable">
        <tr><th>A</th></tr>
        <tr><td>1</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert len(tables) == 1
    assert tables[0].columns == ["A"]


def test_empty_cells_become_empty_strings():
    html = """
    <table class="wikitable">
        <tr><th>A</th><th>B</th></tr>
        <tr><td>1</td><td></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["1", ""]]


def test_multiple_tables_get_sequential_ids():
    html = """
    <table class="wikitable"><tr><th>A</th></tr><tr><td>1</td></tr></table>
    <table class="wikitable"><tr><th>B</th></tr><tr><td>2</td></tr></table>
    """

    tables = extract_tables(html)

    assert len(tables) == 2
    assert tables[0].id == "table-0"
    assert tables[1].id == "table-1"


def test_no_tables_returns_empty_list():
    assert extract_tables("<p>No tables here.</p>") == []


def test_empty_html_returns_empty_list():
    assert extract_tables("") == []


def test_table_with_only_header_row_has_no_rows():
    html = """
    <table class="wikitable">
        <tr><th>A</th><th>B</th></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].columns == ["A", "B"]
    assert tables[0].rows == []
    
def test_multiple_inline_elements_in_cell_get_space_separated():
    html = """
    <table class="wikitable">
        <tr><th>Type</th><th>Values</th></tr>
        <tr><td>bool</td><td><code>True</code><code>False</code></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["bool", "True False"]]