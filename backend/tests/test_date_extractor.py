from app.extractors.date_extractor import extract_dates


def test_modern_date_with_iso():
    html = """
    <table class="infobox">
      <tr>
        <td class="infobox-label">Born</td>
        <td class="infobox-data">
          (<span class="bday">1879-03-14</span>) 14 March 1879
        </td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 1
    assert events[0].title == "Born"
    assert events[0].date == "1879-03-14"
    assert events[0].date_precision.value == "day"


def test_iso_without_bday_class():
    html = """
    <table class="infobox">
      <tr>
        <td class="infobox-label">Died</td>
        <td class="infobox-data">18 April 1955 (1955-04-18) (aged 76)</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert events[0].date == "1955-04-18"


def test_bce_date_extracts_year_only():
    html = """
    <table class="infobox">
      <tr>
        <td class="infobox-label">Born</td>
        <td class="infobox-data">c. 470 BC Deme Alopece, Athens</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 1
    assert events[0].date == "-0470"
    assert events[0].date_precision.value == "year"


def test_bce_without_circa():
    html = """
    <table class="infobox">
      <tr>
        <td class="infobox-label">Died</td>
        <td class="infobox-data">399 BC (aged approx. 71) Athens</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert events[0].date == "-0399"


def test_bce_and_ce_marker_both_supported():
    html = """
    <table class="infobox">
      <tr><td class="infobox-label">A</td><td class="infobox-data">100 BC</td></tr>
      <tr><td class="infobox-label">B</td><td class="infobox-data">100 BCE</td></tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 2
    assert events[0].date == "-0100"
    assert events[1].date == "-0100"


def test_multiple_dates_get_sequential_ids():
    html = """
    <table class="infobox">
      <tr><td class="infobox-label">Born</td><td class="infobox-data">(1879-03-14)</td></tr>
      <tr><td class="infobox-label">Died</td><td class="infobox-data">(1955-04-18)</td></tr>
    </table>
    """

    events = extract_dates(html)

    assert events[0].id == "event-0"
    assert events[1].id == "event-1"


def test_row_without_date_is_ignored():
    html = """
    <table class="infobox">
      <tr><td class="infobox-label">Occupation</td><td class="infobox-data">Physicist</td></tr>
    </table>
    """

    assert extract_dates(html) == []


def test_no_infobox_returns_empty_list():
    assert extract_dates("<p>No infobox here.</p>") == []


def test_empty_html_returns_empty_list():
    assert extract_dates("") == []


def test_russian_th_td_structure_is_supported():
    html = """
    <table class="infobox">
      <tr>
        <th class="plainlist">Дата рождения</th>
        <td class="plainlist">14 марта 1879 (1879-03-14)</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 1
    assert events[0].date == "1879-03-14"
    assert events[0].title == "Дата рождения"


def test_russian_bce_notation():
    html = """
    <table class="infobox">
      <tr>
        <th class="plainlist">Дата рождения</th>
        <td class="plainlist">около 469 до н. э.</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 1
    assert events[0].date == "-0469"
    assert events[0].date_precision.value == "year"


def test_russian_bce_without_spaces_in_notation():
    html = """
    <table class="infobox">
      <tr>
        <th class="plainlist">Дата смерти</th>
        <td class="plainlist">81 год до н.э.</td>
      </tr>
    </table>
    """

    events = extract_dates(html)

    assert events[0].date == "-0081"


def test_ordinary_wikitable_is_ignored():
    html = """
    <table class="wikitable">
      <tr><th>Historian</th><th>Estimated year</th></tr>
      <tr><td>Some Historian</td><td>753 BC</td></tr>
    </table>
    """

    assert extract_dates(html) == []


def test_navbox_is_ignored():
    html = """
    <table class="navbox">
      <tr><td>Ancient Greek philosophy</td><td>560 BC</td></tr>
    </table>
    """

    assert extract_dates(html) == []


def test_infobox_dates_found_even_with_other_tables_present():
    html = """
    <table class="wikitable">
      <tr><td>Noise</td><td>100 BC</td></tr>
    </table>
    <table class="infobox">
      <tr><td class="infobox-label">Born</td><td class="infobox-data">(1879-03-14)</td></tr>
    </table>
    <table class="navbox">
      <tr><td>Noise</td><td>200 BC</td></tr>
    </table>
    """

    events = extract_dates(html)

    assert len(events) == 1
    assert events[0].date == "1879-03-14"


# --- Даты инфобокса без ISO-записи (сессия 2б) ---------------------------------


def _row(label, value):
    return f'<table class="infobox"><tr><th class="infobox-label">{label}</th><td class="infobox-data">{value}</td></tr></table>'


def test_text_date_without_iso_is_extracted():
    # Brazil: "• Declaration | 7 September 1822" - ISO-записи нет.
    events = extract_dates(_row("• Declaration", "7 September 1822"))

    assert [(e.title, e.date, e.date_precision.value) for e in events] == [("• Declaration", "1822-09-07", "day")]


def test_russian_text_date_without_iso_is_extracted():
    events = extract_dates(_row("Основано", "18 января 1871 года (Германская империя)"))

    assert [(e.date, e.date_precision.value) for e in events] == [("1871-01-18", "day")]


def test_us_format_date_without_iso_is_extracted():
    events = extract_dates(_row("Founded", "September 4, 1998; 27 years ago"))

    assert [e.date for e in events] == ["1998-09-04"]


def test_range_takes_first_full_date():
    # World War II: "1 September 1939 – 2 September 1945".
    events = extract_dates(_row("Date", "1 September 1939 – 2 September 1945 (6 years, 1 day)"))

    assert [e.date for e in events] == ["1939-09-01"]


def test_iso_is_preferred_over_text_date():
    events = extract_dates(_row("Born", "14 March 1879 (1879-03-14) Ulm"))

    assert [e.date for e in events] == ["1879-03-14"]


def test_bce_year_without_day_still_works():
    events = extract_dates(_row("Дата рождения", "около 469 до н. э."))

    assert [(e.date, e.date_precision.value) for e in events] == [("-0469", "year")]


def test_value_without_any_date_gives_no_event():
    assert extract_dates(_row("Capital", "Paris")) == []
