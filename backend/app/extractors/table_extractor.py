import re

from bs4 import BeautifulSoup

from app.extractors.text_utils import is_footnote_marker, strings_without_footnotes
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
        # Текст склеивается как в исходном HTML, лишние пробелы сжимаются:
        # пробел между "<i>…</i> <span>(Linnaeus, 1758)</span>" сохраняется.
        title = (
            " ".join("".join(strings_without_footnotes(caption_tag)).split())
            if caption_tag
            else None
        )

        all_rows = raw_table.find_all("tr")
        if not all_rows:
            continue

        notes: list[str] = []

        # Строки <td> во всю ширину над шапкой (Tokyo: "Статистика населения ...").
        # Переосмысливаются, только если за ними идёт настоящая шапка из
        # одних <th>; иначе (Julius Caesar, "Political offices" над
        # данными) поведение прежнее: первая строка - колонки.
        start = 0
        while start < len(all_rows) and _is_full_width(all_rows[start], tag="td"):
            start += 1
        if start > 0 and not _is_header_row(all_rows[start] if start < len(all_rows) else None):
            start = 0
        for tr in all_rows[:start]:
            text = _cell_text(tr.find(["th", "td"]))
            if title is None:
                title = text
            else:
                notes.append(text)

        header_end = _header_end(all_rows, start)
        columns = _header_columns(all_rows[start:header_end])

        # Строки во всю ширину под данными (Tokyo: "Источник: ...").
        end = len(all_rows)
        while end > header_end and _is_full_width(all_rows[end - 1]):
            end -= 1
        trailing = [_cell_text(tr.find(["th", "td"])) for tr in all_rows[end:]]

        rows = _data_rows(all_rows[header_end:end])

        tables.append(
            Table(
                id=f"table-{index}",
                title=title,
                columns=columns,
                rows=rows,
                notes=notes + trailing,
            )
        )

    return tables


def _span(cell, name: str) -> int:
    try:
        return max(1, int(cell.get(name, 1)))
    except ValueError:
        return 1


def _is_full_width(tr, tag: str | None = None) -> bool:
    """
    Строка из одной ячейки на несколько колонок: пояснение или примечание.
    tag="td" отсекает <th colspan> над шапкой - это заголовок группы
    колонок ("Population" над "1990 | 2000"), а не пояснение.
    """
    cells = tr.find_all(["th", "td"])
    return (
        len(cells) == 1
        and _span(cells[0], "colspan") > 1
        and (tag is None or cells[0].name == tag)
    )


def _is_header_row(tr) -> bool:
    if tr is None:
        return False
    cells = tr.find_all(["th", "td"])
    return bool(cells) and all(cell.name == "th" for cell in cells)


def _header_end(all_rows, start: int) -> int:
    """
    Индекс первой строки после шапки. Шапка - строка start; следующая
    строка из одних <th> входит в шапку, только если в предыдущей
    строке шапки есть объединённая ячейка (colspan > 1), ждущая
    подзаголовков (Tokyo: "Возраст" -> "до 15 | 15—64 | от 65").
    Иначе строки, начинающиеся с <th> (Julius Caesar: "58 BC"),
    остаются данными, как и раньше.
    """
    end = start + 1
    while (
        end < len(all_rows)
        and _is_header_row(all_rows[end])
        and any(_span(cell, "colspan") > 1 for cell in all_rows[end - 1].find_all(["th", "td"]))
    ):
        end += 1
    return end


def _header_columns(header_rows) -> list[str]:
    """
    Названия колонок из одной или нескольких строк шапки с учётом
    colspan/rowspan: ячейки раскладываются по сетке, название колонки -
    тексты сверху вниз через " — " без повторов ("Возраст — до 15").
    """
    grid: list[dict[int, str]] = [dict() for _ in header_rows]
    for row_index, tr in enumerate(header_rows):
        column = 0
        for cell in tr.find_all(["th", "td"]):
            while column in grid[row_index]:
                column += 1
            text = _cell_text(cell)
            rowspan = min(_span(cell, "rowspan"), len(header_rows) - row_index)
            for r in range(row_index, row_index + rowspan):
                for c in range(column, column + _span(cell, "colspan")):
                    grid[r][c] = text
            column += _span(cell, "colspan")

    if len(header_rows) == 1:
        # Одна строка шапки - как раньше: по колонке на ячейку.
        return [_cell_text(cell) for cell in header_rows[0].find_all(["th", "td"])]

    width = max((max(row) + 1 for row in grid if row), default=0)
    columns = []
    for c in range(width):
        parts: list[str] = []
        for row in grid:
            text = row.get(c, "")
            if text and (not parts or parts[-1] != text):
                parts.append(text)
        columns.append(" — ".join(parts))
    return columns


def _data_rows(trs) -> list[list[str]]:
    """
    Строки данных с раскрытыми объединёнными ячейками: значение ячейки
    с rowspan повторяется в следующих строках (Julius Caesar: "Gallic
    Wars" на 12 строк), с colspan - в соседних колонках, как в
    стандартных инструментах разбора таблиц. Без этого значения
    съезжали в чужие колонки. rowspan за пределы таблицы обрезается.
    """
    rows: list[list[str]] = []
    # Колонка -> (текст, сколько ещё строк занимает) от rowspan сверху.
    carried: dict[int, tuple[str, int]] = {}
    for tr in trs:
        cells = tr.find_all(["td", "th"])
        if not cells and not carried:
            continue
        row: dict[int, str] = {}
        for column, (text, remaining) in list(carried.items()):
            row[column] = text
            if remaining > 1:
                carried[column] = (text, remaining - 1)
            else:
                del carried[column]
        column = 0
        for cell in cells:
            while column in row:
                column += 1
            text = _cell_text(cell)
            rowspan = _span(cell, "rowspan")
            for c in range(column, column + _span(cell, "colspan")):
                row[c] = text
                if rowspan > 1:
                    carried[c] = (text, rowspan - 1)
            column += _span(cell, "colspan")
        if row:
            rows.append([row.get(c, "") for c in range(max(row) + 1)])
    return rows


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


def _code_ancestor(node, cell):
    """Ближайший <code>, содержащий текстовый узел, в пределах ячейки."""
    parent = node.parent
    while parent is not None and parent is not cell:
        if parent.name == "code":
            return parent
        parent = parent.parent
    return None


def _cell_text(cell) -> str:
    """
    Извлекает текст ячейки, склеивая содержимое нескольких вложенных
    элементов (например, <code>True</code><code>False</code>) через
    пробел, а не впритык, и исключая скрытые sort-key spans
    (style="display:none"), которые MediaWiki добавляет для корректной
    числовой/датовой сортировки таблиц - без фильтрации их текст
    (например, "03699428.&&&&00") склеивается с видимым значением
    ("3 699 428"), портя данные. Маркеры сносок (<sup class="reference">,
    например "[107]") тоже отбрасываются, а текст внутри одного <code>
    не разрывается пробелами.
    """
    pieces: list[str] = []
    current_code = None
    for text in cell.strings:
        if _is_hidden(text, cell) or is_footnote_marker(text, cell):
            continue
        code = _code_ancestor(text, cell)
        if code is not None and code is current_code:
            # Подсветка синтаксиса дробит одно выражение на <span>'ы:
            # внутри одного <code> куски склеиваются как есть,
            # со своими пробелами, а не через пробел.
            pieces[-1] += text
            continue
        current_code = code
        pieces.append(text)

    return " ".join(piece.strip() for piece in pieces if piece.strip())
