import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from app.models import Image

_THUMB_WIDTH_RE = re.compile(r"/\d+px-")


def _normalize_url(url: str) -> str:
    """Протокол-независимый URL (//upload.wikimedia.org/...) -> https://..."""
    if url.startswith("//"):
        return "https:" + url
    return url


def _upsize_url(thumbnail_url: str, width: int = 1280) -> str:
    """
    Заменяет размер в URL превью на более крупный (тот же CDN-путь).
    Если паттерн размера не найден - возвращает исходный URL без изменений
    (известное упрощение: не гарантирует "истинный оригинал").
    """
    return _THUMB_WIDTH_RE.sub(f"/{width}px-", thumbnail_url, count=1)


def _file_title(container) -> str | None:
    """Извлекает имя файла из ссылки на страницу File: - используется для дедупликации."""
    link = container.find("a", class_="mw-file-description")
    if link and link.get("href", "").startswith("/wiki/File:"):
        return unquote(link["href"][len("/wiki/File:"):])
    return None


def extract_images(html: str) -> list[Image]:
    """
    Извлекает изображения (§14 ТЗ) из тела статьи (div.thumb, исключая
    карты mw-kartographer-map) и из infobox (td.infobox-image).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    images: list[Image] = []
    seen: set[str] = set()

    containers: list[tuple[str, object]] = [
        ("body", div)
        for div in soup.find_all("div", class_="thumb")
        if not div.find(class_="mw-kartographer-map")
    ]

    infobox_cell = soup.find("td", class_="infobox-image")
    if infobox_cell is not None:
        containers.append(("infobox", infobox_cell))

    for kind, container in containers:
        img_tag = container.find("img")
        if img_tag is None or not img_tag.get("src"):
            continue

        thumbnail_url = _normalize_url(img_tag["src"])
        url = _upsize_url(thumbnail_url)
        alt = img_tag.get("alt") or None

        caption = None
        if kind == "body":
            caption_tag = container.find(class_="thumbcaption")
            if caption_tag:
                caption = " ".join(caption_tag.stripped_strings) or None
        else:  # infobox: подпись, если есть, в следующей строке таблицы
            row = container.find_parent("tr")
            next_row = row.find_next_sibling("tr") if row else None
            if next_row:
                caption_cell = next_row.find(class_="infobox-caption")
                if caption_cell:
                    caption = " ".join(caption_cell.stripped_strings) or None

        dedup_key = _file_title(container) or thumbnail_url
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        images.append(
            Image(url=url, thumbnail_url=thumbnail_url, caption=caption, alt=alt)
        )

    return images