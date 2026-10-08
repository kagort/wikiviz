import re

from bs4 import BeautifulSoup

from app.extractors.section_extractor import HEADING_TAGS, extract_sections
from app.models import DatePrecision, Event, SourceType

_EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

_RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

_EN_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})\s+(?P<month>" + "|".join(_EN_MONTHS) + r")\s+(?P<year>\d{1,4})\b",
    re.IGNORECASE,
)

# Американский формат "Month Day, Year": "July 4, 1776".
_US_DATE_RE = re.compile(
    r"\b(?P<month>" + "|".join(_EN_MONTHS) + r")\s+(?P<day>\d{1,2}),\s+(?P<year>\d{1,4})\b",
    re.IGNORECASE,
)

_RU_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})\s+(?P<month>" + "|".join(_RU_MONTHS) + r")\s+(?P<year>\d{1,4})\s*(?:года?|г\.)?",
    re.IGNORECASE,
)

# Маркер эпохи сразу после найденной даты (ТЗ §16.2): "100 BC",
# "44 BCE", "44 года до н. э.", "100 г. до н.э.", "до Р. Х.".
_BCE_MARKER_RE = re.compile(
    r"\s*(?:года?\s*|г\.\s*)?(?:BCE?\b|до\s*н\.?\s*э\.?|до\s*Р\.?\s*Х\.?)",
    re.IGNORECASE,
)

_TEXT_CONFIDENCE = 0.6
_LEAD_TITLE = "Introduction"

_EXCLUDED_SECTION_TITLES = {
    "references", "citations", "bibliography", "notes", "footnotes",
    "external links", "further reading", "see also", "sources",
    "примечания", "источники", "литература", "ссылки", "см. также",
    "сноски", "примечания и источники",
}


def _month_number(month_text: str):
    key = month_text.lower()
    return _EN_MONTHS.get(key) or _RU_MONTHS.get(key)


def _strip_tables(fragment_html: str) -> str:
    """Убирает содержимое <table> перед поиском дат - таблицы (списки
    стран-членов, списки должностных лиц и т.п.) дают систематический
    шум и не являются "упоминанием в прозе"."""
    soup = BeautifulSoup(fragment_html, "html.parser")
    for table in soup.find_all("table"):
        table.decompose()
    return " ".join(soup.stripped_strings)


def _lead_text(soup: BeautifulSoup) -> str:
    headings = soup.find_all(HEADING_TAGS)
    if not headings:
        return _strip_tables(str(soup))

    first_heading = headings[0]
    wrapper = first_heading.find_parent("div", class_="mw-heading")
    boundary = wrapper if wrapper is not None else first_heading

    preceding = list(reversed(boundary.find_previous_siblings()))
    fragment_html = "".join(str(el) for el in preceding if getattr(el, "name", None))
    return _strip_tables(fragment_html)


def parse_text_dates(text: str) -> list[tuple[str, DatePrecision]]:
    """
    Полные даты в тексте в порядке появления: "14 March 1879",
    "July 4, 1776", "14 марта 1879 года". Дата с маркером эпохи
    до н. э. сохраняется только годом ("-0044", precision=year, ТЗ §16.2).
    Используется и для текста статьи, и для ячеек инфобокса без ISO-записи.
    """
    matches = []
    for pattern in (_EN_DATE_RE, _US_DATE_RE, _RU_DATE_RE):
        for match in pattern.finditer(text):
            month = _month_number(match.group("month"))
            day = int(match.group("day"))
            if month is None or not (1 <= day <= 31):
                continue
            matches.append((match.start(), match, month, day))

    result = []
    for _, match, month, day in sorted(matches, key=lambda item: item[0]):
        year = int(match.group("year"))
        if _BCE_MARKER_RE.match(text, match.end()):
            # До н. э. хранится только год (ТЗ §16.2): день и месяц
            # в таких датах часто неоднозначны ("12 or 13 July 100 BC").
            result.append((f"-{year:04d}", DatePrecision.YEAR))
        else:
            result.append((f"{year:04d}-{month:02d}-{day:02d}", DatePrecision.DAY))
    return result


def _find_dates_in_text(text: str, title: str) -> list[Event]:
    events: list[Event] = []
    seen: set[str] = set()

    for date_str, precision in parse_text_dates(text):
        if date_str in seen:
            continue
        seen.add(date_str)
        events.append(
            Event(
                id="pending",
                date=date_str,
                date_precision=precision,
                title=title,
                source=SourceType.ARTICLE_TEXT,
                confidence=_TEXT_CONFIDENCE,
            )
        )

    return events


def extract_text_dates(html: str) -> list[Event]:
    """
    Извлекает даты (день+месяц+год) из обычного текста статьи через
    словарь названий месяцев (en/ru), без NLP-анализа смысла предложения.

    Исключения (добавлены после обнаружения систематического шума на
    реальной статье "Организация Объединённых Наций" - см. историю):
    - служебные разделы (References/Citations/Примечания/Источники и
      т.п.) вместе со всеми их подразделами - содержат даты обращения
      к источникам и публикаций, не события статьи;
    - содержимое <table> внутри раздела - таблицы (список стран-членов,
      список должностных лиц) дают систематический шум и обрабатываются
      отдельно как структурированные данные, не как "упоминание в прозе".

    Дата привязывается к заголовку раздела, где встретилась, либо к
    "Introduction" для текста до первого заголовка. confidence=0.6
    (ниже, чем у дат из infobox) - привязка к заголовку раздела заведомо
    менее точна, чем привязка к конкретному infobox-полю.

    Дата с маркером эпохи до н. э. сохраняется только годом ("-0044",
    precision=year), как и в infobox (ТЗ §16.2).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    events: list[Event] = []

    lead_text = _lead_text(soup)
    events.extend(_find_dates_in_text(lead_text, title=_LEAD_TITLE))

    # Уровень заголовка открытого служебного раздела: его подразделы
    # (например, Economy/Government/Culture внутри External links у France,
    # Secondary sources внутри Sources) исключаются вместе с ним, хотя
    # их собственные названия служебными не выглядят.
    excluded_level = None
    for section in extract_sections(html):
        if excluded_level is not None and section.level > excluded_level:
            continue
        excluded_level = None
        if section.title.strip().lower() in _EXCLUDED_SECTION_TITLES:
            excluded_level = section.level
            continue
        section_text = _strip_tables(section.html)
        events.extend(_find_dates_in_text(section_text, title=section.title))

    for index, event in enumerate(events):
        event.id = f"text-event-{index}"

    return events
