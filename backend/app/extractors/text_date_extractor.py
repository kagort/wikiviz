import re

from bs4 import BeautifulSoup, Comment

from app.extractors.context import SectionIndex, block_of
from app.extractors.section_extractor import HEADING_TAGS
from app.models import DatePrecision, Event, SourceType, ValueContext

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



def _month_number(month_text: str):
    key = month_text.lower()
    return _EN_MONTHS.get(key) or _RU_MONTHS.get(key)


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


def _text_blocks(soup):
    """
    Текст статьи по блокам в порядке документа: [(блок, вид, текст)].
    Блок - абзац, пункт списка, подпись иллюстрации или другой родитель
    (context.block_of). Пропускаются таблицы (структурированные данные,
    не "упоминание в прозе"), заголовки, стили и комментарии.
    """
    groups: dict[int, list] = {}
    for node in soup.find_all(string=True):
        if isinstance(node, Comment) or node.parent.name in ("style", "script"):
            continue
        if not node.strip():
            continue
        if node.find_parent(HEADING_TAGS) is not None or node.find_parent("table") is not None:
            continue
        block, kind = block_of(node)
        group = groups.setdefault(id(block), [block, kind, []])
        group[2].append(node.strip())
    return [(block, kind, " ".join(parts)) for block, kind, parts in groups.values()]


def extract_text_dates(html: str) -> list[Event]:
    """
    Извлекает даты (день+месяц+год) из обычного текста статьи через
    словарь названий месяцев (en/ru), без NLP-анализа смысла предложения.

    Исключения (добавлены после обнаружения систематического шума на
    реальной статье "Организация Объединённых Наций" - см. историю):
    - служебные разделы (References/Citations/Примечания/Источники и
      т.п.) вместе со всеми их подразделами - содержат даты обращения
      к источникам и публикаций, не события статьи;
    - содержимое <table> - таблицы (список стран-членов, список
      должностных лиц) дают систематический шум и обрабатываются
      отдельно как структурированные данные, не как "упоминание в прозе".

    Даты ищутся внутри блока (абзац, пункт списка, подпись) - дата не
    склеивается из соседних блоков. У события записывается происхождение
    (context): вид блока и путь разделов - по нему слой отбора отличает,
    например, даты из списков наград от дат в рассказе.

    Дата привязывается к заголовку раздела, где встретилась, либо к
    "Introduction" для текста до первого заголовка. confidence=0.6
    (ниже, чем у дат из infobox) - привязка к заголовку раздела заведомо
    менее точна, чем привязка к конкретному infobox-полю. Повтор одной
    даты в пределах раздела не добавляется.

    Дата с маркером эпохи до н. э. сохраняется только годом ("-0044",
    precision=year), как и в infobox (ТЗ §16.2).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    index = SectionIndex(soup)

    events: list[Event] = []
    seen: dict[tuple, set[str]] = {}

    for block, kind, text in _text_blocks(soup):
        path, service = index.section_of(block)
        if service:
            continue
        section_seen = seen.setdefault(tuple(path), set())
        for date_str, precision in parse_text_dates(text):
            if date_str in section_seen:
                continue
            section_seen.add(date_str)
            events.append(
                Event(
                    id=f"text-event-{len(events)}",
                    date=date_str,
                    date_precision=precision,
                    title=path[-1] if path else _LEAD_TITLE,
                    source=SourceType.ARTICLE_TEXT,
                    confidence=_TEXT_CONFIDENCE,
                    context=ValueContext(block=kind, section_path=path),
                )
            )

    return events
