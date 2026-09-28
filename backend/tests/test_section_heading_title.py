from app.extractors.section_extractor import extract_sections


def test_footnote_marker_is_excluded_from_title():
    """
    Regression-тест: на реальной статье "Токио" (ru) заголовок раздела
    содержал маркер сноски - "Города-побратимы[39]" вместо
    "Города-побратимы". Маркер лежит в <sup class="reference">
    внутри <h2>, а get_text() собирал текст всех вложенных элементов.
    """
    html = (
        '<div class="mw-heading mw-heading2">'
        '<h2 id="sister">Города-побратимы'
        '<sup id="cite_ref-39" class="reference"><a href="#cite_note-39">[39]</a></sup>'
        '</h2></div><p>text</p>'
    )

    sections = extract_sections(html)

    assert sections[0].title == "Города-побратимы"


def test_edit_link_inside_heading_is_excluded_from_title():
    """В старой разметке ссылка [edit] лежит внутри самого заголовка."""
    html = (
        '<h2>History<span class="mw-editsection"><a href="#">edit</a></span></h2>'
        '<p>text</p>'
    )

    sections = extract_sections(html)

    assert sections[0].title == "History"


def test_ordinary_superscript_in_title_is_kept():
    """Обычный <sup> (не сноска) - часть названия и должен остаться."""
    html = '<h2>E = mc<sup>2</sup></h2><p>text</p>'

    sections = extract_sections(html)

    assert sections[0].title == "E = mc2"


def test_inline_elements_in_title_keep_spaces():
    """Пробелы вокруг вложенных тегов не должны теряться."""
    html = '<h2>Python <i>and</i> C</h2><p>text</p>'

    sections = extract_sections(html)

    assert sections[0].title == "Python and C"