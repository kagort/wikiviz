import re

from bs4 import BeautifulSoup

from app.models import Table

_HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none")


def extract_tables(html: str) -> list[Table]:
    """
    Извлекает информационные таблицы Wikipedia (§12 ТЗ).

    Ищет только <table class="wikitable"> - так MediaWiki размечает
    "настоящие" таблицы с данными, в отличие от infobox и navbox,
    которые тоже являются <table>, но обрабатываются другими extractors
    (или не обрабатываются вовсе).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    raw_tables = soup.find_all("table", class_="wikitable")

    tables = []
    for index, raw_table in enumerate(raw_tables):
        caption_tag = raw_table.find("caption")
        title = caption_tag.get_text(strip=True) if caption_tag else None

        all_rows = raw_table.find_all("tr")
        if not all_rows:
            continue

        header_cells = all_rows[0].find_all(["th", "td"])
        columns = [_cell_text(cell) for cell in header_cells]

        rows = []
        for tr in all_rows[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row = [_cell_text(cell) for cell in cells]
            rows.append(row)

        tables.append(
            Table(
                id=f"table-{index}",
                title=title,
                columns=columns,
                rows=rows,
            )
        )

    return tables


def _is_hidden(node, cell) -> bool:
    """
    Проверяет, находится ли текстовый узел внутри элемента с
    style="display:none" в пределах данной ячейки (не выходя за её
    границы вверх по дереву).
    """
    parent = node.parent
    while parent is not None:
        style = parent.get("style", "") if hasattr(parent, "get") else ""
        if _HIDDEN_STYLE_RE.search(style):
            return True
        if parent is cell:
            break
        parent = parent.parent
    return False


def _cell_text(cell) -> str:
    """
    Извлекает текст ячейки, склеивая содержимое нескольких вложенных
    элементов (например, <code>True</code><code>False</code>) через
    пробел, а не впритык, и исключая скрытые sort-key spans
    (style="display:none"), которые MediaWiki добавляет для корректной
    числовой/датовой сортировки таблиц - без фильтрации их текст
    (например, "03699428.&&&&00") склеивается с видимым значением
    ("3 699 428"), портя данные.
    """
    visible = [
        text.strip()
        for text in cell.strings
        if text.strip() and not _is_hidden(text, cell)
    ]
    return " ".join(visible)