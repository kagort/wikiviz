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

_RU_COMBINED_DMS_RE = re.compile(
    r"(?P<lat_deg>\d+)°(?:(?P<lat_min>\d+)′)?(?:(?P<lat_sec>\d+(?:\.\d+)?)″)?"
    r"\s*(?P<lat_dir>с\.?\s*ш\.?|ю\.?\s*ш\.?)"
    r"\s*"
    r"(?P<lon_deg>\d+)°(?:(?P<lon_min>\d+)′)?(?:(?P<lon_sec>\d+(?:\.\d+)?)″)?"
    r"\s*(?P<lon_dir>в\.?\s*д\.?|з\.?\s*д\.?)",
    re.IGNORECASE,
)


def _dms_to_decimal(degrees: int, minutes: int, seconds: float, direction: str) -> float:
    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ("S", "W"):
        decimal = -decimal
    return decimal


def _dms_text_to_decimal(text: str) -> float:
    match = _DMS_RE.search(text)
    if not match:
        raise ValueError(f"Cannot parse DMS coordinate: {text!r}")
    return _dms_to_decimal(
        int(match.group("deg")),
        int(match.group("min")) if match.group("min") else 0,
        float(match.group("sec")) if match.group("sec") else 0.0,
        match.group("dir"),
    )


def _extract_name(lat_span, fallback: str) -> str:
    link = lat_span.find_parent("a", href=re.compile(r"geohack\.toolforge\.org"))
    if link is None:
        return fallback

    query = parse_qs(urlparse(link["href"]).query)
    raw_title = query.get("title", [""])[0]
    if not raw_title:
        return fallback

    title = unquote(raw_title).replace("+", " ")
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    return title or fallback


def _extract_english_style(soup: BeautifulSoup, article_title: str):
    """Английская разметка: раздельные span.latitude / span.longitude."""
    lat_spans = soup.find_all(class_="latitude")
    lon_spans = soup.find_all(class_="longitude")

    for lat_span, lon_span in zip(lat_spans, lon_spans):
        try:
            latitude = _dms_text_to_decimal(lat_span.get_text(strip=True))
            longitude = _dms_text_to_decimal(lon_span.get_text(strip=True))
        except ValueError:
            continue
        name = _extract_name(lat_span, fallback=article_title)
        yield latitude, longitude, name


def _extract_russian_style(soup: BeautifulSoup, article_title: str):
    """
    Русская разметка: span.coordinates с широтой и долготой в ОДНОМ тексте
    ("35°42′ с.ш. 139°36′ в.д."), кириллические сокращения направлений.
    geohack-ссылка в русской версии не содержит параметр title - имя
    точки всегда берётся из заголовка статьи (известное ограничение:
    несколько координат на одной ru-странице получат одинаковое имя).
    """
    for wrapper in soup.find_all("span", class_="coordinates"):
        text_span = wrapper.find("span")
        if text_span is None:
            continue

        text = text_span.get_text(" ", strip=True).replace("\xa0", " ")
        match = _RU_COMBINED_DMS_RE.search(text)
        if not match:
            continue

        lat_dir_raw = match.group("lat_dir").lower()
        lon_dir_raw = match.group("lon_dir").lower()
        lat_direction = "S" if lat_dir_raw.startswith("ю") else "N"
        lon_direction = "W" if lon_dir_raw.startswith("з") else "E"

        latitude = _dms_to_decimal(
            int(match.group("lat_deg")),
            int(match.group("lat_min")) if match.group("lat_min") else 0,
            float(match.group("lat_sec")) if match.group("lat_sec") else 0.0,
            lat_direction,
        )
        longitude = _dms_to_decimal(
            int(match.group("lon_deg")),
            int(match.group("lon_min")) if match.group("lon_min") else 0,
            float(match.group("lon_sec")) if match.group("lon_sec") else 0.0,
            lon_direction,
        )

        yield latitude, longitude, article_title


def extract_coordinates(html: str, article_title: str) -> list[Location]:
    """
    Извлекает координаты (§13 ТЗ) из HTML статьи.

    Поддерживает два независимых варианта разметки, обнаруженных на
    практике:
    1. Английская Wikipedia: раздельные span.latitude / span.longitude,
       имя точки - из title соседней geohack-ссылки, с fallback на
       заголовок статьи.
    2. Русская Wikipedia: единый span.coordinates с широтой и долготой
       в одном тексте, кириллические сокращения направлений (с.ш./ю.ш./
       в.д./з.д.). geohack-ссылка в этом варианте не содержит title -
       имя точки всегда берётся из заголовка статьи.

    Оба пути объединяются в общий список с единой дедупликацией.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    locations: list[Location] = []
    seen_coords: set[tuple[float, float]] = set()

    for latitude, longitude, name in list(_extract_english_style(soup, article_title)) + list(
        _extract_russian_style(soup, article_title)
    ):
        dedup_key = (round(latitude, 5), round(longitude, 5))
        if dedup_key in seen_coords:
            continue
        seen_coords.add(dedup_key)

        locations.append(
            Location(
                id=f"location-{len(locations)}",
                name=name,
                latitude=latitude,
                longitude=longitude,
            )
        )

    return locations
