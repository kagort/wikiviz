import re
from typing import Optional

from bs4 import BeautifulSoup

from app.models import NumericValue, SourceType

_FOOTNOTE_RE = re.compile(r"\[\s*[^\]]{1,6}\s*\]")
_ARROW_RE = re.compile(r"[▲▼]")

_MULTIPLIERS = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
    "quadrillion": 1_000_000_000_000_000,
    "quintillion": 1_000_000_000_000_000_000,
    "тысяча": 1_000, "тыс": 1_000,
    "миллион": 1_000_000, "млн": 1_000_000,
    "миллиард": 1_000_000_000, "млрд": 1_000_000_000,
    "триллион": 1_000_000_000_000, "трлн": 1_000_000_000_000,
    "квадриллион": 1_000_000_000_000_000, "квадрлн": 1_000_000_000_000_000,
}

_MULTIPLIER_WORD_RE = re.compile(
    "(" + "|".join(sorted((re.escape(k) for k in _MULTIPLIERS), key=len, reverse=True)) + r")\.?",
    re.IGNORECASE,
)

_NUMBER_EN_PATTERN = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+"
_NUMBER_RU_PATTERN = r"\d{1,3}(?:[ \u00a0]\d{3})+(?:,\d+)?|\d+,\d+|\d+"

_NUMBER_EN_RE = re.compile(_NUMBER_EN_PATTERN)
_NUMBER_RU_RE = re.compile(_NUMBER_RU_PATTERN)

_UNIT_RE = re.compile(r"[^\s\d(\[]{1,15}")
_SUPERSCRIPT_RE = re.compile(r"([23])(?!\d)")


def _clean(text: str) -> str:
    text = _FOOTNOTE_RE.sub("", text)
    text = _ARROW_RE.sub("", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_label(text: str) -> str:
    text = text.lstrip("•").strip()
    return _clean(text)


def _to_float(raw: str, language: str) -> float:
    if language == "ru":
        cleaned = raw.replace(" ", "").replace(",", ".")
    else:
        cleaned = raw.replace(",", "")
    return float(cleaned)


def _extract_unit(rest: str, label_text: str) -> Optional[str]:
    if rest.startswith("%"):
        return "%"
    if "(%)" in label_text:
        return "%"

    unit_match = _UNIT_RE.match(rest)
    if not unit_match:
        return None

    candidate = unit_match.group(0).strip()
    if not candidate:
        return None

    after_unit = rest[unit_match.end():].lstrip()
    sup_match = _SUPERSCRIPT_RE.match(after_unit)
    if sup_match and any(ch.isalpha() for ch in candidate):
        candidate += "²" if sup_match.group(1) == "2" else "³"

    return candidate


def _extract_single_value(
    label: str, label_text: str, cleaned_data: str, language: str
) -> Optional[NumericValue]:
    number_re = _NUMBER_RU_RE if language == "ru" else _NUMBER_EN_RE

    match = number_re.search(cleaned_data)
    if not match:
        return None

    value = _to_float(match.group(0), language)
    rest = cleaned_data[match.end():].lstrip()

    mult_match = _MULTIPLIER_WORD_RE.match(rest)
    if mult_match:
        multiplier_key = mult_match.group(1).lower()
        value *= _MULTIPLIERS[multiplier_key]
        rest = rest[mult_match.end():].lstrip()

    unit = _extract_unit(rest, label_text)

    if unit is None and re.fullmatch(r"\d{4}", match.group(0)) and 1000 <= value <= 2100:
        unit = "year"

    return NumericValue(label=label, value=value, unit=unit, source=SourceType.INFOBOX)


def _extract_percent_breakdown(
    label: str, cleaned_data: str, language: str
) -> list[NumericValue]:
    number_pattern = _NUMBER_RU_PATTERN if language == "ru" else _NUMBER_EN_PATTERN
    pattern = re.compile(rf"({number_pattern})\s*%\s*([^\d%]+?)(?=\d|$)")

    matches = list(pattern.finditer(cleaned_data))
    if len(matches) < 2:
        return []

    results = []
    for match in matches:
        value = _to_float(match.group(1), language)
        descriptor = match.group(2).strip(" .,")
        if not descriptor:
            continue
        results.append(
            NumericValue(
                label=f"{label} — {descriptor}",
                value=value,
                unit="%",
                source=SourceType.INFOBOX,
            )
        )
    return results


def extract_numbers(html: str, language: str = "en") -> list[NumericValue]:
    """
    Извлекает числовые данные (§17 ТЗ) ИСКЛЮЧИТЕЛЬНО из infobox
    (<table class="infobox">) - та же изоляция от wikitable/navbox, что
    и у DateExtractor, по тем же причинам (риск ложных срабатываний из
    общих шаблонов и вспомогательных таблиц).

    language определяет локаль разделителей: "en" - запятая=тысячи,
    точка=десятичная; "ru" - пробел=тысячи, запятая=десятичная.

    Строки группируются по ближайшему предшествующему заголовку группы
    (<th class="infobox-header">, например "Area"/"Population"/"GDP") -
    иначе повторяющиеся generic-label вроде "Total" неразличимы между
    собой (обнаружено на реальной статье France, где "•Total" встречается
    трижды в разных смысловых группах).

    Для обычных (не-процентных) ячеек берётся ТОЛЬКО первое найденное
    число - это одновременно отсекает ранги в скобках ("(21st)"),
    дублирующее представление в другой системе единиц ("sq mi" после
    "km²") и номера сносок, поскольку все они в реальных данных всегда
    идут ПОСЛЕ основного значения.

    Множители (million/billion/трлн/млрд и т.п.) распознаются сразу
    после числа и раскрываются в полное значение (не остаются частью
    unit) - это удобнее для последующей визуализации на графике
    (StatisticsChart), где widget не должен разбирать текст единицы
    измерения, чтобы понять масштаб числа.

    Ячейки с несколькими парами "число%+описание" (например, разбивка
    религий) обрабатываются отдельно - извлекаются все пары, а не
    только первая.

    Известные ограничения: год, к которому относится значение (поле
    "year" модели), не заполняется - эта информация обычно уже есть
    текстом в label (например, "January 2026 estimate"); восстановление
    надстрочных степеней (km², km³) работает только для степеней 2 и 3.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find("table", class_="infobox")
    if infobox is None:
        return []

    results: list[NumericValue] = []
    current_group: Optional[str] = None

    for row in infobox.find_all("tr"):
        cells = row.find_all(["th", "td"])

        if len(cells) == 1:
            cell = cells[0]
            if "infobox-header" in (cell.get("class") or []):
                current_group = _clean_label(cell.get_text(" ", strip=True))
            continue

        if len(cells) != 2:
            continue

        label_cell, data_cell = cells
        label_text = _clean_label(label_cell.get_text(" ", strip=True))
        label = f"{current_group} — {label_text}" if current_group else label_text

        cleaned_data = _clean(data_cell.get_text(" ", strip=True))
        if not cleaned_data:
            continue

        breakdown = _extract_percent_breakdown(label, cleaned_data, language)
        if breakdown:
            results.extend(breakdown)
            continue

        single = _extract_single_value(label, label_text, cleaned_data, language)
        if single is not None:
            results.append(single)

    return results
