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


def test_english_bc_date_keeps_only_negative_year():
    # ТЗ §16.2: для дат до н. э. извлекается только год, "-000N".
    html = """
    <h2>Early life</h2>
    <p>Caesar was born on 12 or 13 July 100 BC in Rome.</p>
    """

    events = extract_text_dates(html)

    assert len(events) == 1
    assert events[0].date == "-0100"
    assert events[0].date_precision.value == "year"


def test_english_bce_marker_is_recognized():
    html = """
    <h2>Death</h2>
    <p>He was assassinated on 15 March 44 BCE.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.date_precision.value) for e in events] == [("-0044", "year")]


def test_russian_bc_date_with_goda_keeps_only_negative_year():
    html = """
    <h2>Смерть</h2>
    <p>Убит 15 марта 44 года до н. э. в Риме.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.date_precision.value) for e in events] == [("-0044", "year")]


def test_russian_bc_date_compact_marker_is_recognized():
    html = """
    <h2>Биография</h2>
    <p>Родился 13 июля 100 г. до н.э.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.date_precision.value) for e in events] == [("-0100", "year")]


def test_ad_date_next_to_bc_date_is_unchanged():
    html = """
    <h2>Legacy</h2>
    <p>He died on 15 March 44 BC. A statue was unveiled on 1 January 2000.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.date_precision.value) for e in events] == [
        ("-0044", "year"),
        ("2000-01-01", "day"),
    ]


def test_subsections_of_excluded_section_are_excluded():
    # France: подразделы External links называются Economy/Government/Culture,
    # сами по себе служебными не выглядят.
    html = """
    <div class="mw-heading mw-heading2"><h2>External links</h2></div>
    <ul><li>Official site</li></ul>
    <div class="mw-heading mw-heading3"><h3>Culture</h3></div>
    <ul><li>Journal. Archived 27 August 2007 at the Wayback Machine.</li></ul>
    """

    events = extract_text_dates(html)

    assert events == []


def test_deeply_nested_subsections_of_excluded_section_are_excluded():
    html = """
    <h2>Sources</h2>
    <h3>Secondary sources</h3>
    <p>Published 26 January 2021.</p>
    <h4>Articles</h4>
    <p>Retrieved 2 September 2017.</p>
    """

    events = extract_text_dates(html)

    assert events == []


def test_russian_subsections_of_excluded_section_are_excluded():
    html = """
    <h2>Литература</h2>
    <h3>Статьи</h3>
    <p>Опубликовано 21 мая 2015 года.</p>
    """

    events = extract_text_dates(html)

    assert events == []


def test_section_after_excluded_subtree_is_included_again():
    html = """
    <h2>Notes</h2>
    <h3>Details</h3>
    <p>Accessed 1 May 2020.</p>
    <h2>Legacy</h2>
    <p>A monument was opened on 14 July 1990.</p>
    <h3>Memorials</h3>
    <p>Another one on 3 March 1995.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.title) for e in events] == [
        ("1990-07-14", "Legacy"),
        ("1995-03-03", "Memorials"),
    ]


def test_us_format_date_is_recognized():
    # "Month Day, Year": статьи на американском английском (United States, Google).
    html = """
    <h2>History</h2>
    <p>The Declaration of Independence was adopted on July 4, 1776, in Philadelphia.</p>
    """

    events = extract_text_dates(html)

    assert [(e.date, e.date_precision.value) for e in events] == [("1776-07-04", "day")]


def test_us_format_bc_date_keeps_only_negative_year():
    html = """
    <h2>Death</h2>
    <p>He was killed on March 15, 44 BC.</p>
    """

    assert [(e.date, e.date_precision.value) for e in extract_text_dates(html)] == [("-0044", "year")]


def test_mixed_formats_keep_order_of_appearance():
    html = """
    <h2>Timeline</h2>
    <p>Founded on September 4, 1998; incorporated 4 September 1999; listed on August 19, 2004.</p>
    """

    assert [e.date for e in extract_text_dates(html)] == ["1998-09-04", "1999-09-04", "2004-08-19"]


# --- Происхождение дат: context (сессия 4, решение В2) --------------------------


def _ctx(event):
    return (event.context.block.value, event.context.section_path, event.context.service_section)


def test_context_tells_list_item_from_paragraph():
    # Гагарин: даты наград - пункты списка, даты биографии - абзацы.
    html = """
    <h2>Biography</h2>
    <p>He flew on 12 April 1961.</p>
    <h2>Awards</h2>
    <ul><li>Hero of the Soviet Union, 14 April 1961</li></ul>
    """

    events = extract_text_dates(html)

    assert [(e.date, _ctx(e)) for e in events] == [
        ("1961-04-12", ("paragraph", ["Biography"], False)),
        ("1961-04-14", ("list_item", ["Awards"], False)),
    ]


def test_context_section_path_follows_nesting():
    html = """
    <div class="mw-heading mw-heading2"><h2>History</h2></div>
    <div class="mw-heading mw-heading3"><h3>Early years</h3></div>
    <p>Founded on 4 September 1998.</p>
    <div class="mw-heading mw-heading2"><h2>Products</h2></div>
    <p>Launched on 1 April 2004.</p>
    """

    assert [e.context.section_path for e in extract_text_dates(html)] == [
        ["History", "Early years"],
        ["Products"],
    ]


def test_context_of_lead_dates_has_empty_path():
    html = "<p>Born on 14 March 1879.</p><h2>Life</h2><p>x</p>"

    events = extract_text_dates(html)

    assert events[0].title == "Introduction"
    assert _ctx(events[0]) == ("paragraph", [], False)


def test_context_of_date_in_figure_caption():
    html = """
    <h2>Life</h2>
    <figure typeof="mw:File/Thumb"><img src="x.jpg"/><figcaption>Photo taken on 1 May 1920</figcaption></figure>
    """

    assert [_ctx(e) for e in extract_text_dates(html)] == [("figure", ["Life"], False)]


def test_dates_from_neighbouring_blocks_are_not_glued_together():
    # "15 March" в конце одного абзаца и "1879" в начале следующего - не дата.
    html = "<h2>A</h2><p>It happened on 15 March</p><p>1879 people came.</p>"

    assert extract_text_dates(html) == []
