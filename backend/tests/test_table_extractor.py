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


def test_hidden_sort_key_span_is_excluded_from_cell_text():
    """
    Regression-тест: MediaWiki добавляет в ячейки таблиц скрытый
    sort-key span (style="display:none") для корректной числовой
    сортировки. Обнаружено на реальной статье "Токио" (ru) —
    без фильтрации текст скрытого span склеивался с видимым значением
    ("03699428.&&&&00 3 699 428" вместо "3 699 428").
    """
    html = """
    <table class="wikitable">
        <tr><th>Год</th><th>Население</th></tr>
        <tr>
            <td>1920</td>
            <td><span style="display:none">03699428.0000</span> 3 699 428</td>
        </tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["1920", "3 699 428"]]


def test_hidden_span_nested_deeper_than_direct_child_is_excluded():
    """
    Скрытый span может быть не прямым потомком ячейки, а обёрнут
    дополнительным тегом - фильтрация должна работать на любой глубине.
    """
    html = """
    <table class="wikitable">
        <tr><th>A</th></tr>
        <tr><td><b><span style="display:none">99</span></b> 5</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["5"]]


def test_style_with_other_properties_is_not_treated_as_hidden():
    """
    Только display:none скрывает содержимое - другие style-свойства
    (например, text-align) не должны исключать текст.
    """
    html = """
    <table class="wikitable">
        <tr><th>A</th></tr>
        <tr><td><span style="text-align: center;">visible</span></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["visible"]]

def test_footnote_markers_are_excluded_from_data_cells():
    # Разметка MediaWiki одинакова в en и ru: <sup class="reference">.
    html = """
    <table class="wikitable">
        <tr><th>Type</th><th>Size</th></tr>
        <tr><td>int<sup id="cite_ref-1" class="reference"><a href="#cite_note-1">[107]</a></sup></td><td>42</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["int", "42"]]


def test_footnote_markers_are_excluded_from_header_cells():
    html = """
    <table class="wikitable">
        <tr><th>Население<sup class="reference"><a href="#cite_note-24">[24]</a></sup></th><th>Год</th></tr>
        <tr><td>14 000 000</td><td>2024</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].columns == ["Население", "Год"]


def test_footnote_markers_are_excluded_from_table_caption():
    html = """
    <table class="wikitable">
        <caption>Climate<sup class="reference"><a href="#cite_note-3">[3]</a></sup></caption>
        <tr><th>Month</th></tr>
        <tr><td>Jan</td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].title == "Climate"


def test_non_reference_superscript_is_kept():
    # Обычный <sup> (степень, порядковый номер) - часть данных, не сноска.
    html = """
    <table class="wikitable">
        <tr><th>Area</th></tr>
        <tr><td>2194 km<sup>2</sup></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["2194 km 2"]]


def test_syntax_highlighted_code_is_not_split_by_spaces():
    # Реальная разметка Wikipedia: подсветка синтаксиса дробит одно
    # выражение на <span>'ы внутри <code class="mw-highlight">.
    html = """
    <table class="wikitable">
        <tr><th>Type</th><th>Example</th></tr>
        <tr><td>bytearray</td><td><code class="mw-highlight mw-highlight-lang-python" dir="ltr"><span class="nb">bytearray</span><span class="p">(</span><span class="sa">b</span><span class="s1">'Some ASCII'</span><span class="p">)</span></code></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["bytearray", "bytearray(b'Some ASCII')"]]


def test_spaces_inside_highlighted_code_are_preserved():
    html = """
    <table class="wikitable">
        <tr><th>Example</th></tr>
        <tr><td><code class="mw-highlight"><span class="p">{</span><span class="s1">'key1'</span><span class="p">:</span> <span class="mf">1.0</span><span class="p">,</span> <span class="mi">3</span><span class="p">:</span> <span class="kc">False</span><span class="p">}</span></code></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["{'key1': 1.0, 3: False}"]]


def test_separate_highlighted_code_elements_stay_space_separated():
    # Несколько примеров кода в одной ячейке (через <br/>) не склеиваются.
    html = """
    <table class="wikitable">
        <tr><th>Example</th></tr>
        <tr><td><code class="mw-highlight"><span class="p">{</span><span class="mi">4.0</span><span class="p">}</span></code><br/><code class="mw-highlight"><span class="nb">set</span><span class="p">()</span></code></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["{4.0} set()"]]


def test_code_next_to_plain_text_stays_space_separated():
    html = """
    <table class="wikitable">
        <tr><th>Description</th></tr>
        <tr><td>types <code>numpy.byte</code> and <code>numpy.ulonglong</code></td></tr>
    </table>
    """

    tables = extract_tables(html)

    assert tables[0].rows == [["types numpy.byte and numpy.ulonglong"]]


def test_full_width_row_above_header_becomes_title_and_multirow_header_is_merged():
    # Tokyo, "Статистика населения": пояснение во всю ширину, затем шапка
    # в две строки (rowspan=2 у большинства колонок, "Возраст" с colspan=3).
    html = """
    <table class="wikitable">
        <tr><td colspan="5">Статистика населения Токио</td></tr>
        <tr><th rowspan="2">Перепись</th><th rowspan="2">Население</th><th colspan="3">Возраст</th></tr>
        <tr><th>до 15</th><th>15—64</th><th>от 65</th></tr>
        <tr><td>1 октября 1920</td><td>3 699 428</td><td>31,6%</td><td>65,3%</td><td>3,2%</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.title == "Статистика населения Токио"
    assert table.columns == [
        "Перепись",
        "Население",
        "Возраст — до 15",
        "Возраст — 15—64",
        "Возраст — от 65",
    ]
    assert table.rows == [["1 октября 1920", "3 699 428", "31,6%", "65,3%", "3,2%"]]
    assert table.notes == []


def test_full_width_row_above_header_goes_to_notes_when_caption_exists():
    html = """
    <table class="wikitable">
        <caption>Население</caption>
        <tr><td colspan="2">Данные переписей</td></tr>
        <tr><th>Год</th><th>Население</th></tr>
        <tr><td>1920</td><td>3 699 428</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.title == "Население"
    assert table.columns == ["Год", "Население"]
    assert table.rows == [["1920", "3 699 428"]]
    assert table.notes == ["Данные переписей"]


def test_full_width_source_row_below_data_goes_to_notes():
    # Tokyo, "Климат Токио": последняя строка "Источник: ..." во всю ширину.
    html = """
    <table class="wikitable">
        <caption>Климат Токио</caption>
        <tr><th>Показатель</th><th>Янв.</th><th>Год</th></tr>
        <tr><th>Средняя температура, °C</th><td>6,1</td><td>16,3</td></tr>
        <tr><td colspan="3">Источник: Погода и климат</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.columns == ["Показатель", "Янв.", "Год"]
    assert table.rows == [["Средняя температура, °C", "6,1", "16,3"]]
    assert table.notes == ["Источник: Погода и климат"]


def test_full_width_row_without_header_below_keeps_old_behavior():
    # Julius Caesar, таблица должностей: "Political offices" во всю ширину,
    # но за ней не шапка, а данные - строку не переосмысливаем.
    html = """
    <table class="wikitable">
        <tr><th colspan="3">Political offices</th></tr>
        <tr><td>Preceded by A</td><td>Roman consul 59 BC</td><td>Succeeded by B</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.title is None
    assert table.columns == ["Political offices"]
    assert table.rows == [["Preceded by A", "Roman consul 59 BC", "Succeeded by B"]]
    assert table.notes == []


def test_row_header_cells_in_data_rows_are_not_treated_as_header():
    # Julius Caesar, таблица сражений: строки данных начинаются с <th>.
    html = """
    <table class="wikitable">
        <tr><th>Date</th><th>War</th></tr>
        <tr><th>58 BC</th><td>Gallic Wars</td></tr>
        <tr><th>57 BC</th><td>Gallic Wars</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.columns == ["Date", "War"]
    assert table.rows == [["58 BC", "Gallic Wars"], ["57 BC", "Gallic Wars"]]


def test_two_level_header_without_rowspan_joins_parent_and_child():
    html = """
    <table class="wikitable">
        <tr><th colspan="2">Population</th></tr>
        <tr><th>1990</th><th>2000</th></tr>
        <tr><td>10</td><td>12</td></tr>
    </table>
    """

    table = extract_tables(html)[0]

    assert table.columns == ["Population — 1990", "Population — 2000"]
    assert table.rows == [["10", "12"]]


def test_tables_without_full_width_rows_have_empty_notes():
    html = """
    <table class="wikitable">
        <tr><th>A</th></tr>
        <tr><td>1</td></tr>
    </table>
    """

    assert extract_tables(html)[0].notes == []
