from app.extractors.number_extractor import extract_numbers


def _infobox(rows_html: str) -> str:
    return f'<table class="infobox">{rows_html}</table>'


def test_simple_integer_en():
    html = _infobox("""
        <tr><td class="infobox-label">Population</td><td class="infobox-data">69,081,996</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert len(result) == 1
    assert result[0].label == "Population"
    assert result[0].value == 69081996.0
    assert result[0].unit is None


def test_decimal_with_unit_and_superscript_km2():
    html = _infobox("""
        <tr><th class="infobox-header">Area</th></tr>
        <tr><td class="infobox-label">•\xa0Total</td>
            <td class="infobox-data">632,702.3\xa0km 2 (244,287.7\xa0sq\xa0mi)</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert len(result) == 1
    assert result[0].label == "Area — Total"
    assert result[0].value == 632702.3
    assert result[0].unit == "km²"


def test_percent_implied_by_label_not_value():
    html = _infobox("""
        <tr><th class="infobox-header">Area</th></tr>
        <tr><td class="infobox-label">•\xa0Water\xa0(%)</td>
            <td class="infobox-data">0.86 [ 4 ]</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert result[0].label == "Area — Water (%)"
    assert result[0].value == 0.86
    assert result[0].unit == "%"


def test_rank_and_footnote_are_ignored_first_match_wins():
    html = _infobox("""
        <tr><th class="infobox-header">Population</th></tr>
        <tr><td class="infobox-label">•\xa0January 2026 estimate</td>
            <td class="infobox-data">69,081,996 [ 7 ] ( 21st )</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert len(result) == 1
    assert result[0].value == 69081996.0
    assert result[0].unit is None


def test_density_unit_with_slash_and_superscript():
    html = _infobox("""
        <tr><th class="infobox-header">Population</th></tr>
        <tr><td class="infobox-label">•\xa0Density</td>
            <td class="infobox-data">109/km 2 (283/sq mi) ( 106th )</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert result[0].value == 109.0
    assert result[0].unit == "/km²"


def test_repeated_generic_label_disambiguated_by_group():
    html = _infobox("""
        <tr><th class="infobox-header">Area</th></tr>
        <tr><td class="infobox-label">•\xa0Total</td><td class="infobox-data">632,702.3\xa0km 2</td></tr>
        <tr><th class="infobox-header">Population</th></tr>
        <tr><td class="infobox-label">•\xa0Total</td><td class="infobox-data">69,081,996</td></tr>
    """)
    result = extract_numbers(html, language="en")
    labels = [r.label for r in result]
    assert "Area — Total" in labels
    assert "Population — Total" in labels


def test_multiplier_trillion_english():
    html = _infobox("""
        <tr><td class="infobox-label">Total</td><td class="infobox-data">$4.734 trillion [ 8 ]</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert result[0].value == 4734000000000.0


def test_multiplier_trln_russian():
    html = _infobox("""
        <tr><td class="infobox-label">Итого (2024)</td>
            <td class="infobox-data">▲ 4,359\xa0трлн [ 7 ]\xa0долл.</td></tr>
    """)
    result = extract_numbers(html, language="ru")
    assert result[0].value == 4359000000000.0
    assert result[0].unit == "долл."


def test_russian_thousands_and_decimal_separators():
    html = _infobox("""
        <tr><td class="infobox-label">Плотность</td>
            <td class="infobox-data">2193,96 км²</td></tr>
    """)
    result = extract_numbers(html, language="ru")
    assert result[0].value == 2193.96


def test_percent_breakdown_multiple_values():
    html = _infobox("""
        <tr><td class="infobox-label">Religion</td>
            <td class="infobox-data">50% Christianity 47% Catholicism 2% Protestantism</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert len(result) == 3
    labels_values = {r.label: r.value for r in result}
    assert labels_values["Religion — Christianity"] == 50.0
    assert labels_values["Religion — Catholicism"] == 47.0
    assert labels_values["Religion — Protestantism"] == 2.0


def test_percent_breakdown_multiword_descriptor():
    html = _infobox("""
        <tr><td class="infobox-label">Religion</td>
            <td class="infobox-data">33% no religion 4% Islam</td></tr>
    """)
    result = extract_numbers(html, language="en")
    labels = [r.label for r in result]
    assert "Religion — no religion" in labels
    assert "Religion — Islam" in labels


def test_bare_four_digit_year_gets_year_unit():
    html = _infobox("""
        <tr><td class="infobox-label">Established</td><td class="infobox-data">1457</td></tr>
    """)
    result = extract_numbers(html, language="en")
    assert result[0].value == 1457.0
    assert result[0].unit == "year"


def test_ordinary_wikitable_is_ignored():
    html = """
    <table class="wikitable">
      <tr><td>Some Historian</td><td>753</td></tr>
    </table>
    """
    assert extract_numbers(html) == []


def test_navbox_is_ignored():
    html = """
    <table class="navbox">
      <tr><td>Founded</td><td>1945</td></tr>
    </table>
    """
    assert extract_numbers(html) == []


def test_row_without_number_is_ignored():
    html = _infobox("""
        <tr><td class="infobox-label">Currency</td><td class="infobox-data">Euro</td></tr>
    """)
    assert extract_numbers(html) == []


def test_no_infobox_returns_empty_list():
    assert extract_numbers("<p>No infobox here.</p>") == []


def test_empty_html_returns_empty_list():
    assert extract_numbers("") == []


def test_source_is_always_infobox():
    html = _infobox("""
        <tr><td class="infobox-label">Population</td><td class="infobox-data">1,000</td></tr>
    """)
    result = extract_numbers(html)
    assert result[0].source.value == "infobox"
