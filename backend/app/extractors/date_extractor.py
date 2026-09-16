import re

from bs4 import BeautifulSoup

from app.models import DatePrecision, Event, SourceType

_ISO_DATE_RE = re.compile(r"\((\d{4})-(\d{2})-(\d{2})\)")
_BCE_YEAR_RE = re.compile(
    r"(?:c\.\s*)?(?:около\s*)?(?P<year>\d{1,4})\s*"
    r"(?:год[а-я]*\s*)?"
    r"(?:BCE?\b|до\s*н\.?\s*э\.?|до\s*Р\.?\s*Х\.?)",
    re.IGNORECASE,
)


def extract_dates(html: str) -> list[Event]:
    """
    Извлекает даты (§16 ТЗ) ИСКЛЮЧИТЕЛЬНО из infobox (<table class="infobox">).

    Сознательно не рассматривает обычные wikitable и, тем более, navbox
    (навигационные шаблоны внизу статьи) как источник - они дают слишком
    много ложных срабатываний: строки из общих для многих статей шаблонов
    (например, "Federations/Confederations" с одинаковой датой сразу у
    Socrates и Aristotle - явный признак общего navbox, а не содержания
    конкретной статьи), либо таблицы, где строка означает не "событие",
    а, например, "историк -> предполагаемая им дата" (как в статье
    Founding of Rome), что не соответствует семантике Event.

    Даты из обычного текста статьи (не infobox/таблиц) обрабатываются
    ОТДЕЛЬНО - см. text_date_extractor.py.

    Строка infobox трактуется как пара (label, data) - первые две ячейки
    строки (<th> или <td>, без привязки к конкретному тегу или классу),
    поскольку верстка отличается между локалями: англ. Wikipedia использует
    два <td> (infobox-label/infobox-data), рус. Wikipedia - <th>+<td>
    (оба класса "plainlist").

    Два независимых пути:
    1. Современные даты: ISO-паттерн (YYYY-MM-DD) в скобках - precision=day.
    2. Даты до нашей эры: текстовый паттерн BC/BCE/"до н. э." - только
       год, precision=year.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    infobox = soup.find("table", class_="infobox")
    if infobox is None:
        return []

    events: list[Event] = []

    rows = infobox.find_all("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        if len(cells) != 2:
            continue
        label_cell, data_cell = cells

        title = label_cell.get_text(strip=True)
        raw_text_for_iso = data_cell.get_text()
        visible_text = " ".join(data_cell.stripped_strings)

        iso_match = _ISO_DATE_RE.search(raw_text_for_iso)
        if iso_match:
            year, month, day = iso_match.groups()
            events.append(
                Event(
                    id=f"event-{len(events)}",
                    date=f"{year}-{month}-{day}",
                    date_precision=DatePrecision.DAY,
                    title=title,
                    source=SourceType.INFOBOX,
                )
            )
            continue

        bce_match = _BCE_YEAR_RE.search(visible_text)
        if bce_match:
            year = int(bce_match.group("year"))
            events.append(
                Event(
                    id=f"event-{len(events)}",
                    date=f"-{year:04d}",
                    date_precision=DatePrecision.YEAR,
                    title=title,
                    source=SourceType.INFOBOX,
                )
            )

    return events
