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
    Извлекает даты (§16 ТЗ) из infobox.

    Строка infobox трактуется как пара (label, data) - первые две ячейки
    строки (<th> или <td>, без привязки к конкретному тегу или классу),
    поскольку верстка отличается между локалями: англ. Wikipedia использует
    два <td> (infobox-label/infobox-data), рус. Wikipedia - <th>+<td>
    (оба класса "plainlist").

    Два независимых пути:
    1. Современные даты: ISO-паттерн (YYYY-MM-DD) в скобках - даёт
       полную точность day. Работает одинаково в en/ru Wikipedia.
    2. Даты до нашей эры: готового машиночитаемого формата нет,
       извлекается только год через текстовый паттерн. Поддерживает
       английскую нотацию (BC/BCE) и русскую ("до н. э.", "до н.э.",
       возможно с "год"/"года" между числом и маркером) - precision=year.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    events: list[Event] = []

    rows = soup.find_all("tr")
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
