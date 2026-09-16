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

_RU_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})\s+(?P<month>" + "|".join(_RU_MONTHS) + r")\s+(?P<year>\d{1,4})\s*(?:года?|г\.)?",
    re.IGNORECASE,
)

_TEXT_CONFIDENCE = 0.6
_LEAD_TITLE = "Introduction"


def _month_number(month_text: str):
    key = month_text.lower()
    return _EN_MONTHS.get(key) or _RU_MONTHS.get(key)


def _lead_text(soup: BeautifulSoup) -> str:
    """
    Текст статьи до первого заголовка - extract_sections() его
    игнорирует (задокументированное ограничение с Phase 3), но именно
    там часто живут ключевые вводные факты.
    """
    headings = soup.find_all(HEADING_TAGS)
    if not headings:
        return " ".join(soup.stripped_strings)

    first_heading = headings[0]
    wrapper = first_heading.find_parent("div", class_="mw-heading")
    boundary = wrapper if wrapper is not None else first_heading

    preceding = list(reversed(boundary.find_previous_siblings()))
    parts = [el.get_text(" ", strip=True) for el in preceding if getattr(el, "name", None)]
    return " ".join(parts)


def _find_dates_in_text(text: str, title: str) -> list[Event]:
    events: list[Event] = []
    seen: set[str] = set()

    for pattern in (_EN_DATE_RE, _RU_DATE_RE):
        for match in pattern.finditer(text):
            month = _month_number(match.group("month"))
            if month is None:
                continue
            day = int(match.group("day"))
            year = int(match.group("year"))
            if not (1 <= day <= 31):
                continue

            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            if date_str in seen:
                continue
            seen.add(date_str)

            events.append(
                Event(
                    id="pending",
                    date=date_str,
                    date_precision=DatePrecision.DAY,
                    title=title,
                    source=SourceType.ARTICLE_TEXT,
                    confidence=_TEXT_CONFIDENCE,
                )
            )

    return events


def extract_text_dates(html: str) -> list[Event]:
    """
    Извлекает даты (день+месяц+год) из обычного текста статьи - НЕ из
    infobox и НЕ из таблиц (это отдельный date_extractor.py) - через
    словарь названий месяцев (en/ru), без NLP-анализа смысла предложения.

    Дата привязывается к заголовку раздела, где встретилась (используя
    ту же разбивку на разделы, что и section_extractor), либо к condition
    "Introduction" для текста до первого заголовка. Это не "название
    события", а лучшее доступное приближение без понимания смысла
    предложения - поэтому confidence ниже (0.6), чем у дат из infobox (1.0).

    Известное ограничение: год без дня/месяца (например, одинокое "BC"-
    упоминание в прозе) не извлекается - только полные даты день-месяц-год.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    events: list[Event] = []

    lead_text = _lead_text(soup)
    events.extend(_find_dates_in_text(lead_text, title=_LEAD_TITLE))

    for section in extract_sections(html):
        section_soup = BeautifulSoup(section.html, "html.parser")
        section_text = " ".join(section_soup.stripped_strings)
        events.extend(_find_dates_in_text(section_text, title=section.title))

    for index, event in enumerate(events):
        event.id = f"text-event-{index}"

    return events
