import re
from typing import Optional

from bs4 import BeautifulSoup

from app.extractors.text_date_extractor import _EN_MONTHS, _RU_MONTHS
from app.models import NumericValue, SourceType

_FOOTNOTE_RE = re.compile(r"\[\s*[^\]]{1,6}\s*\]")
_ARROW_RE = re.compile(r"[▲▼]")

_DATE_LIKE_RE = re.compile(
    r"\b\d{1,2}\s+(?:" + "|".join(_EN_MONTHS) + "|" + "|".join(_RU_MONTHS) + r")\b"
    r"|\b\d{1,2}\.\d{1,2}\.\d{4}\b",
    re.IGNORECASE,
)

_YEAR_SUBHEADER_RE = re.compile(
    r"^(?P<year>\d{4})\s+(?:estimate|estimat\w*|оценка)\.?$",
    re.IGNORECASE,
)

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


def _has_coordinates(data_cell) -> bool:
    if data_cell.find(class_="latitude") or data_cell.find(class_="longitude"):
        return True
    if data_cell.find(class_="coordinates"):
        return True
    return False


def _extract_unit(rest: str, label_text: str) -> Optional[str]:
    if rest.startswith("%"):
        return "%"
    if "(%)" in label_text:
        return "%"

    unit_match = _UNIT_RE.match(rest)
    if not unit_match:
        return None

    candidate = unit_match.group(0).strip()
    if not candidate or not any(ch.isalpha() for ch in candidate):
        return None

    after_unit = rest[unit_match.end():].lstrip()
    sup_match = _SUPERSCRIPT_RE.match(after_unit)
    if sup_match:
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
    (<table class="infobox">).

    Группировка по контексту (label префикс "Группа — ..."):
    - через <th class="infobox-header"> (Area/Population/...) - типовой случай;
    - через строку-подзаголовок вида "GDP (PPP)" / "2026 estimate" -
      обнаружено на реальной статье France: такие подсекции НЕ используют
      infobox-header, а являются обычной двухъячеечной строкой, чьё
      значение - это просто год (+ слово "estimate"/"оценка"), не
      самостоятельная метрика. Такая строка распознаётся эвристически
      (после очистки данные состоят ТОЛЬКО из 4-значного года и
      опционального маркера) и трактуется как новая группа, а не
      как NumericValue.

    Исключения:
    - координаты - и англ. разметка (span.latitude/longitude), и русская
      (span.coordinates, обнаружено на реальной статье о Токио - другая
      разметка координат, чем в английской Wikipedia);
    - даты без ISO-представления (день+месяц, dd.mm.yyyy);
    - единицы измерения без единой буквы (чистая пунктуация).

    Множители раскрываются в полное значение. Ячейки с несколькими
    парами "число%+описание" обрабатываются отдельно.

    Известные ограничения: (1) координаты в русском infobox проверены
    только на одном примере (Токио) - другие возможные варианты
    разметки могли остаться незамеченными; (2) коды (телефонный, ISO),
    встроенные в текст без даты/координат, всё ещё могут извлекаться
    как формально валидные, но бессмысленные значения; (3) unit иногда
    захватывает случайное следующее слово из прозы ячейки.
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

        if _has_coordinates(data_cell):
            continue

        label_text = _clean_label(label_cell.get_text(" ", strip=True))
        cleaned_data = _clean(data_cell.get_text(" ", strip=True))

        if _YEAR_SUBHEADER_RE.match(cleaned_data):
            current_group = label_text
            continue

        if not cleaned_data:
            continue

        if _DATE_LIKE_RE.search(cleaned_data):
            continue

        label = f"{current_group} — {label_text}" if current_group else label_text

        breakdown = _extract_percent_breakdown(label, cleaned_data, language)
        if breakdown:
            results.extend(breakdown)
            continue

        single = _extract_single_value(label, label_text, cleaned_data, language)
        if single is not None:
            results.append(single)

    return results
