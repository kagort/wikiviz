from app.extractors.text_date_extractor import extract_text_dates


def test_english_date_in_section_body():
    html = """
    <h2>History</h2>
    <p>The organization was signed on 26 June 1945 in San Francisco.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 1
    assert events[0].date == "1945-06-26"
    assert events[0].title == "History"
    assert events[0].date_precision.value == "day"


def test_russian_date_with_goda_suffix():
    html = """
    <h2>История</h2>
    <p>Декларация была подписана 1 января 1942 года.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 1
    assert events[0].date == "1942-01-01"
    assert events[0].title == "История"


def test_russian_date_without_suffix():
    html = """
    <h2>История</h2>
    <p>Сессия открылась 10 января 1946 в Лондоне.</p>
    """

    events = extract_text_dates(html)

    assert events[0].date == "1946-01-10"


def test_lead_paragraph_gets_introduction_title():
    html = """
    <p>Founded on 24 October 1945, the organization grew quickly.</p>
    <h2>History</h2>
    <p>No date here.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 1
    assert events[0].title == "Introduction"
    assert events[0].date == "1945-10-24"


def test_confidence_is_lower_than_infobox():
    html = "<h2>History</h2><p>Signed on 26 June 1945.</p>"

    events = extract_text_dates(html)

    assert events[0].confidence == 0.6


def test_dates_in_different_sections_get_different_titles():
    html = """
    <h2>Founding</h2>
    <p>Signed on 26 June 1945.</p>
    <h2>Later events</h2>
    <p>Entered into force on 24 October 1945.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 2
    assert events[0].title == "Founding"
    assert events[1].title == "Later events"


def test_duplicate_date_in_same_section_not_repeated():
    html = """
    <h2>History</h2>
    <p>Signed on 26 June 1945. Later documents confirm 26 June 1945 as the date.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 1


def test_plain_numbers_without_month_name_are_ignored():
    html = "<h2>Stats</h2><p>Population grew by 15 20 1000 percent.</p>"

    assert extract_text_dates(html) == []


def test_ids_are_sequential_across_lead_and_sections():
    html = """
    <p>Founded 1 January 1900.</p>
    <h2>History</h2>
    <p>Signed 2 February 1950.</p>
    """

    events = extract_text_dates(html)

    assert events[0].id == "text-event-0"
    assert events[1].id == "text-event-1"


def test_empty_html_returns_empty_list():
    assert extract_text_dates("") == []


def test_no_dates_in_text_returns_empty_list():
    html = "<h2>Section</h2><p>Nothing date-related here.</p>"

    assert extract_text_dates(html) == []

def test_tables_inside_section_are_excluded():
    html = """
    <h2>Members</h2>
    <p>Intro text without dates.</p>
    <table class="wikitable">
      <tr><th>Country</th><th>Joined</th></tr>
      <tr><td>Testland</td><td>15 January 1950</td></tr>
    </table>
    """

    events = extract_text_dates(html)

    assert events == []


def test_references_section_is_excluded():
    html = """
    <h2>References</h2>
    <p>Retrieved 15 January 2021.</p>
    """

    events = extract_text_dates(html)

    assert events == []
