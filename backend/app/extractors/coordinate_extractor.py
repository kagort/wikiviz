import re
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from app.models import Location

_DMS_RE = re.compile(
    r"(?P<deg>\d+)°"
    r"(?:(?P<min>\d+)′)?"
    r"(?:(?P<sec>\d+(?:\.\d+)?)″)?"
    r"(?P<dir>[NSEW])"
)


def _dms_to_decimal(text: str) -> float:
    """
    Конвертирует DMS-строку вида '27°59′18″N' или '57°18′N' (без секунд)
    в десятичные градусы со знаком (юг/запад — отрицательные).
    """
    match = _DMS_RE.search(text)
    if not match:
        raise ValueError(f"Cannot parse DMS coordinate: {text!r}")

    degrees = int(match.group("deg"))
    minutes = int(match.group("min")) if match.group("min") else 0
    seconds = float(match.group("sec")) if match.group("sec") else 0.0
    direction = match.group("dir")

    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ("S", "W"):
        decimal = -decimal

    return decimal


def _extract_name(lat_span, fallback: str) -> str:
    """
    Ищет ближайшую ссылку на geohack и берёт из неё параметр title.
    Если title отсутствует (частый случай для единственной координаты
    infobox) — используется fallback (обычно заголовок статьи).
    """
    link = lat_span.find_parent("a", href=re.compile(r"geohack\.toolforge\.org"))
    if link is None:
        return fallback

    query = parse_qs(urlparse(link["href"]).query)
    raw_title = query.get("title", [""])[0]
    if not raw_title:
        return fallback

    title = unquote(raw_title).replace("+", " ")
    # Убираем скобочный суффикс вида "(8848.86 m)"
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    return title or fallback


def extract_coordinates(html: str, article_title: str) -> list[Location]:
    """
    Извлекает координаты (§13 ТЗ) из span.latitude / span.longitude,
    которые генерирует шаблон {{coord}} в MediaWiki.

    article_title используется как имя точки, когда рядом с координатой
    нет geohack-ссылки с параметром title (типичный случай единственной
    координаты в infobox).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    lat_spans = soup.find_all(class_="latitude")
    lon_spans = soup.find_all(class_="longitude")

    locations: list[Location] = []
    for index, (lat_span, lon_span) in enumerate(zip(lat_spans, lon_spans)):
        try:
            latitude = _dms_to_decimal(lat_span.get_text(strip=True))
            longitude = _dms_to_decimal(lon_span.get_text(strip=True))
        except ValueError:
            continue  # пропускаем координату, которую не смогли распарсить

        name = _extract_name(lat_span, fallback=article_title)

        locations.append(
            Location(
                id=f"location-{index}",
                name=name,
                latitude=latitude,
                longitude=longitude,
            )
        )

    return locations