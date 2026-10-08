from app.extractors.infobox_extractor import extract_infobox
from app.models import SourceType


def _pairs(infobox):
    return [(f.group, f.label, f.value) for f in infobox.values()]


def test_english_label_data_rows():
    # en: <th class="infobox-label"> + <td class="infobox-data">
    html = """
    <table class="infobox">
        <tr><th class="infobox-above">Python</th></tr>
        <tr><th class="infobox-label">Designed by</th><td class="infobox-data">Guido van Rossum</td></tr>
        <tr><th class="infobox-label">Developer</th><td class="infobox-data">Python Software Foundation</td></tr>
    </table>
    """

    infobox = extract_infobox(html)

    assert _pairs(infobox) == [
        (None, "Designed by", "Guido van Rossum"),
        (None, "Developer", "Python Software Foundation"),
    ]
    field = infobox["designed_by"]
    assert field.key == "designed_by"
    assert field.source == SourceType.INFOBOX
    assert field.normalized_value is None


def test_english_two_td_rows():
    html = """
    <table class="infobox">
        <tr><td class="infobox-label">Born</td><td class="infobox-data">14 March 1879</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [(None, "Born", "14 March 1879")]


def test_russian_plainlist_rows_and_headers():
    # ru: <th class="plainlist"> + <td class="plainlist">, заголовки групп - infobox-header
    html = """
    <table class="infobox">
        <tr><th class="infobox-header" colspan="2">Расположение</th></tr>
        <tr><th class="plainlist">Страна</th><td class="plainlist">Япония</td></tr>
        <tr><th class="infobox-header" colspan="2">Статистика</th></tr>
        <tr><th class="plainlist">Площадь</th><td class="plainlist">2193,96 км²</td></tr>
        <tr><th class="plainlist">Плотность</th><td class="plainlist">6400,9 чел./км²</td></tr>
    </table>
    """

    infobox = extract_infobox(html)

    assert _pairs(infobox) == [
        ("Расположение", "Страна", "Япония"),
        ("Статистика", "Площадь", "2193,96 км²"),
        ("Статистика", "Плотность", "6400,9 чел./км²"),
    ]
    assert list(infobox) == ["расположение_страна", "статистика_площадь", "статистика_плотность"]


def test_bullet_rows_belong_to_header_and_repeated_labels_get_unique_keys():
    # France: "• Total" и "• Density" повторяются в разных группах.
    html = """
    <table class="infobox">
        <tr><th class="infobox-header" colspan="2">Area</th></tr>
        <tr><th class="infobox-label">• Total</th><td class="infobox-data">632,702.3 km<sup>2</sup></td></tr>
        <tr><th class="infobox-header" colspan="2">Population</th></tr>
        <tr><th class="infobox-label">• 2026 estimate</th><td class="infobox-data">69,081,996</td></tr>
        <tr><th class="infobox-label">• Density</th><td class="infobox-data">109/km<sup>2</sup></td></tr>
        <tr><th class="infobox-label">• Metropolitan</th><td class="infobox-data">66,792,845</td></tr>
        <tr><th class="infobox-label">• Density</th><td class="infobox-data">123/km<sup>2</sup></td></tr>
        <tr><th class="infobox-label">GDP (PPP)</th><td class="infobox-data">2026 estimate</td></tr>
        <tr><th class="infobox-label">• Total</th><td class="infobox-data">$4.734 trillion</td></tr>
        <tr><th class="infobox-label">Currency</th><td class="infobox-data">Euro</td></tr>
    </table>
    """

    infobox = extract_infobox(html)

    assert _pairs(infobox) == [
        ("Area", "Total", "632,702.3 km2"),
        ("Population", "2026 estimate", "69,081,996"),
        ("Population", "Density", "109/km2"),
        ("Population", "Metropolitan", "66,792,845"),
        ("Population", "Density", "123/km2"),
        (None, "GDP (PPP)", "2026 estimate"),
        ("GDP (PPP)", "Total", "$4.734 trillion"),
        (None, "Currency", "Euro"),
    ]
    assert list(infobox) == [
        "area_total",
        "population_2026_estimate",
        "population_density",
        "population_metropolitan",
        "population_density_2",
        "gdp_ppp",
        "gdp_ppp_total",
        "currency",
    ]


def test_bullet_rows_after_plain_label_without_header():
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Government</th><td class="infobox-data">Republic</td></tr>
        <tr><th class="infobox-label">• President</th><td class="infobox-data">Emmanuel Macron</td></tr>
        <tr><th class="infobox-label">Legislature</th><td class="infobox-data">Parliament</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Government", "Republic"),
        ("Government", "President", "Emmanuel Macron"),
        (None, "Legislature", "Parliament"),
    ]


def test_subheader_groups_following_plain_rows():
    # Julius Caesar: td.infobox-subheader "Military career", строки без "•".
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Born</th><td class="infobox-data">100 BC</td></tr>
        <tr><td class="infobox-subheader" colspan="2">Military career</td></tr>
        <tr><th class="infobox-label">Allegiance</th><td class="infobox-data">Roman Republic</td></tr>
        <tr><th class="infobox-label">Branch</th><td class="infobox-data">Roman Army</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Born", "100 BC"),
        ("Military career", "Allegiance", "Roman Republic"),
        ("Military career", "Branch", "Roman Army"),
    ]


def test_header_followed_by_full_width_data_becomes_field():
    # Python: "Influenced by" - заголовок, содержимое во всю ширину строкой ниже.
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">License</th><td class="infobox-data">PSF License</td></tr>
        <tr><th class="infobox-header" colspan="2">Influenced by</th></tr>
        <tr><td class="infobox-full-data" colspan="2">ABC, Ada, ALGOL 68</td></tr>
        <tr><th class="infobox-header" colspan="2">Influenced</th></tr>
        <tr><td class="infobox-full-data" colspan="2">Groovy, Boo</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "License", "PSF License"),
        (None, "Influenced by", "ABC, Ada, ALGOL 68"),
        (None, "Influenced", "Groovy, Boo"),
    ]


def test_footnotes_and_hidden_text_are_removed_from_label_and_value():
    html = """
    <table class="infobox">
        <tr>
            <th class="infobox-label">Religion (2025)<sup class="reference"><a>[b]</a></sup></th>
            <td class="infobox-data">20 February 1991; 35 years ago<span style="display:none"> (<span class="bday">1991-02-20</span>)</span><sup class="reference"><a>[2]</a></sup></td>
        </tr>
        <tr>
            <th class="plainlist">Губернатор</th>
            <td class="plainlist">Юрико Коикэ<sup class="reference"><a>[3]</a></sup></td>
        </tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Religion (2025)", "20 February 1991; 35 years ago"),
        (None, "Губернатор", "Юрико Коикэ"),
    ]


def test_inline_markup_keeps_natural_spacing():
    # Склейка без лишних пробелов перед пунктуацией: "Multi-paradigm: object-oriented,".
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Paradigm</th><td class="infobox-data"><a href="#">Multi-paradigm</a>: <a href="#">object-oriented</a>, <a href="#">procedural</a> (<a href="#">imperative</a>)</td></tr>
        <tr><th class="infobox-label">GDP (<a href="#">PPP</a>)</th><td class="infobox-data">x</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Paradigm", "Multi-paradigm: object-oriented, procedural (imperative)"),
        (None, "GDP (PPP)", "x"),
    ]


def test_list_items_and_line_breaks_are_comma_separated():
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Occupations</th><td class="infobox-data"><div class="plainlist"><ul><li>Politician</li><li>soldier</li><li>author</li></ul></div></td></tr>
        <tr><th class="infobox-label">Died</th><td class="infobox-data">15 March 44 BC<br>Theatre of Pompey, Rome</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Occupations", "Politician, soldier, author"),
        (None, "Died", "15 March 44 BC, Theatre of Pompey, Rome"),
    ]


def test_service_rows_are_skipped():
    # Заголовок над таблицей, картинка, подпись снизу, пустые строки - не поля.
    html = """
    <table class="infobox">
        <tr><th class="infobox-above">France</th></tr>
        <tr><td class="infobox-image"><img src="x.png" alt="Flag"/></td></tr>
        <tr><td class="infobox-full-data"></td></tr>
        <tr><th class="infobox-label">Capital</th><td class="infobox-data">Paris</td></tr>
        <tr><th class="infobox-label">Empty</th><td class="infobox-data"> </td></tr>
        <tr><td class="infobox-below">Python Programming at Wikibooks</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [(None, "Capital", "Paris")]


def test_rows_of_nested_tables_are_not_separate_fields():
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Office</th><td class="infobox-data">
            <table><tr><td>Consul</td></tr><tr><td>59 BC</td></tr></table>
        </td></tr>
        <tr><th class="infobox-label">Awards</th><td class="infobox-data">Civic Crown</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Office", "Consul, 59 BC"),
        (None, "Awards", "Civic Crown"),
    ]


def test_only_first_infobox_is_used():
    html = """
    <table class="infobox"><tr><th class="infobox-label">A</th><td>1</td></tr></table>
    <table class="infobox"><tr><th class="infobox-label">B</th><td>2</td></tr></table>
    """

    assert _pairs(extract_infobox(html)) == [(None, "A", "1")]


def test_numeric_label_gets_non_numeric_key():
    # Ключ из одних цифр JavaScript переставил бы в начало объекта.
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Name</th><td>X</td></tr>
        <tr><th class="infobox-label">2020</th><td>14 000 000</td></tr>
    </table>
    """

    assert list(extract_infobox(html)) == ["name", "field_2020"]


def test_no_infobox_returns_empty_dict():
    assert extract_infobox("<p>Text</p>") == {}
    assert extract_infobox("") == {}


def test_noprint_relative_age_is_removed():
    # "35 years ago" MediaWiki вычисляет при каждом запросе (span.noprint):
    # без исключения фикстура менялась бы каждый день.
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">First appeared</th><td class="infobox-data">20 February 1991<span class="noprint">; 35 years ago</span></td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [(None, "First appeared", "20 February 1991")]


def test_line_break_inside_label_is_a_space_not_a_list():
    # France: "Capital<br>and largest city", "Religion<br>(2025)".
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Capital<br>and largest city</th><td class="infobox-data">Paris</td></tr>
        <tr><th class="infobox-label"><div>Religion<br>(2025)</div></th><td class="infobox-data">48% Christianity</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Capital and largest city", "Paris"),
        (None, "Religion (2025)", "48% Christianity"),
    ]


def test_full_width_image_row_under_header_is_not_a_value():
    # Tokyo: под заголовком "Символика" - картинка флага с подписью.
    html = """
    <table class="infobox">
        <tr><th class="infobox-header" colspan="2">Символика</th></tr>
        <tr><td class="plainlist" colspan="2"><img src="flag.png" alt=""/><br/>Флаг префектуры</td></tr>
        <tr><th class="plainlist">Дерево</th><td class="plainlist">Гинкго</td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [("Символика", "Дерево", "Гинкго")]


def test_list_after_colon_is_not_separated_by_extra_comma():
    # Julius Caesar, Conflicts: "Several, including:" и список под ним.
    html = """
    <table class="infobox">
        <tr><th class="infobox-label">Conflicts</th><td class="infobox-data">Several, including:<div class="plainlist"><ul><li>Siege of Mytilene</li><li>Gallic Wars</li></ul></div></td></tr>
    </table>
    """

    assert _pairs(extract_infobox(html)) == [
        (None, "Conflicts", "Several, including: Siege of Mytilene, Gallic Wars"),
    ]
