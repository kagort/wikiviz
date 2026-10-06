import re
from typing import Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from app.models import InfoboxField, SourceType

_HIDDEN_STYLE_RE = re.compile(r"display\s*:\s*none")
_KEY_RE = re.compile(r"\W+")

# Блочные элементы: на их границах значение делится на части
# ("Politician, soldier, author"), а не склеивается впритык.
_BLOCK_TAGS = {"li", "ul", "ol", "div", "p", "dl", "dd", "dt", "table", "tr", "td", "th"}
_SKIPPED_TAGS = {"style", "script"}
_HEADER_CLASSES = {"infobox-header", "infobox-subheader"}
# Строки, которые не являются полями: заголовок над таблицей, картинка, подпись снизу.
_SERVICE_CLASSES = {"infobox-above", "infobox-image", "infobox-below", "infobox-caption"}

_SEPARATOR = "\x00"
_BULLET = "•"


def _is_skipped(tag: Tag) -> bool:
    """Служебная разметка, текст которой не входит в поле."""
    if tag.name in _SKIPPED_TAGS:
        return True
    classes = tag.get("class") or []
    if tag.name == "sup" and "reference" in classes:
        return True
    # noprint - экранные добавки, например возраст "; 35 years ago",
    # который MediaWiki пересчитывает при каждом запросе.
    if "noprint" in classes:
        return True
    return bool(_HIDDEN_STYLE_RE.search(tag.get("style", "")))


def _collect(node: Tag, parts: list[str]) -> None:
    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if _is_skipped(child):
                continue
            if child.name == "br":
                parts.append(_SEPARATOR)
            elif child.name in _BLOCK_TAGS:
                parts.append(_SEPARATOR)
                _collect(child, parts)
                parts.append(_SEPARATOR)
            else:
                _collect(child, parts)


def _cell_text(cell: Tag, separator: str = ", ") -> str:
    """
    Видимый текст ячейки: без сносок (<sup class="reference">), скрытых
    span'ов (display:none, например ISO-дата "(1991-02-20)") и экранных
    добавок (.noprint, например "; 35 years ago"). Строчная
    разметка склеивается как в исходном HTML, без лишних пробелов перед
    пунктуацией; элементы списков и строки через <br> - через запятую.
    """
    parts: list[str] = []
    _collect(cell, parts)
    pieces = (
        " ".join(piece.replace("﻿", "").split()).strip(" ,;")
        for piece in "".join(parts).split(_SEPARATOR)
    )
    return separator.join(piece for piece in pieces if piece)


def _make_key(group: Optional[str], label: str, used: set[str]) -> str:
    """
    Ключ поля: группа и подпись в нижнем регистре через "_"
    ("Area" + "Total" -> "area_total"); повторы получают суффикс _2, _3.
    Ключ из одних цифр получает префикс: JavaScript переставляет такие
    ключи объекта в начало, и порядок полей бы нарушился.
    """
    text = f"{group} {label}" if group else label
    base = _KEY_RE.sub("_", text.lower()).strip("_") or "field"
    if base.isdigit():
        base = f"field_{base}"

    key = base
    suffix = 2
    while key in used:
        key = f"{base}_{suffix}"
        suffix += 1
    used.add(key)
    return key


def _classes(cell: Tag) -> set[str]:
    return set(cell.get("class") or [])


def extract_infobox(html: str) -> dict[str, InfoboxField]:
    """
    Извлекает поля инфобокса (§11 ТЗ) из первого <table class="infobox">
    (так же, как DateExtractor и NumberExtractor).

    Поле - строка из двух ячеек: первые две ячейки строки (<th> или <td>;
    en: th.infobox-label + td.infobox-data, ru: th.plainlist + td.plainlist).

    Группы (поле group):
    - строка-заголовок (infobox-header, infobox-subheader) открывает группу;
      в ней остаются следующие строки (Tokyo "Статистика", Caesar
      "Military career");
    - строки с "•" относятся к открытой группе, а без неё - к предыдущей
      строке без "•" (France "GDP (PPP)" -> "• Total");
    - строка без "•" после строк с "•" закрывает группу заголовка
      (France: "GDP (PPP)" после пунктов "Population").
    Заголовок, за которым идёт строка во всю ширину с текстом (Python
    "Influenced by"), сам становится полем.

    Строки вложенных таблиц отдельными полями не считаются: их текст
    входит в значение ячейки. Служебные строки (заголовок над таблицей,
    картинки, подпись снизу, пустые) пропускаются.
    """
    if not html or not html.strip():
        return {}

    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", class_="infobox")
    if infobox is None:
        return {}

    fields: dict[str, InfoboxField] = {}
    used_keys: set[str] = set()

    header: Optional[str] = None  # открытая группа из строки-заголовка
    header_has_bullets = False
    parent_label: Optional[str] = None  # последняя строка без "•"
    previous_was_header = False

    def add(group: Optional[str], label: str, value: str) -> None:
        key = _make_key(group, label, used_keys)
        fields[key] = InfoboxField(
            key=key,
            label=label,
            group=group,
            value=value,
            source=SourceType.INFOBOX,
        )

    for row in infobox.find_all("tr"):
        if row.find_parent("table") is not infobox:
            continue
        cells = row.find_all(["th", "td"], recursive=False)
        after_header, previous_was_header = previous_was_header, False

        if len(cells) == 1:
            cell = cells[0]
            classes = _classes(cell)
            text = _cell_text(cell)
            if classes & _HEADER_CLASSES:
                header, header_has_bullets, parent_label = text or None, False, None
                previous_was_header = True
            elif after_header and text and header and not classes & _SERVICE_CLASSES:
                add(None, header, text)
                header = None
            continue

        if len(cells) < 2:
            continue

        # В подписи <br> - перенос строки, а не перечисление.
        raw_label = _cell_text(cells[0], separator=" ")
        is_bullet = raw_label.startswith(_BULLET)
        label = raw_label.lstrip(_BULLET).strip()
        value = _cell_text(cells[1])

        if is_bullet:
            group = header or parent_label
            header_has_bullets = header_has_bullets or header is not None
        else:
            if header is not None and header_has_bullets:
                header = None
            group = header
            parent_label = label

        if label and value:
            add(group, label, value)

    return fields
