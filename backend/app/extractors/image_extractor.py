import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from app.extractors.text_utils import strings_without_footnotes
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


def _caption_text(element) -> str:
    """Подпись: непустые куски текста через пробел, без маркеров сносок."""
    return " ".join(
        text.strip() for text in strings_without_footnotes(element) if text.strip()
    )


def _file_title(container) -> str | None:
    """Извлекает имя файла из ссылки на страницу File: - используется для дедупликации."""
    link = container.find("a", class_="mw-file-description")
    if link and link.get("href", "").startswith("/wiki/File:"):
        return unquote(link["href"][len("/wiki/File:"):])
    return None


# Блоки, картинки внутри которых - не иллюстрации статьи (значки, навигация).
_SKIPPED_ANCESTOR_CLASSES = {"navbox", "side-box", "noprint", "metadata", "sistersitebox", "ambox"}


def _is_body_container(tag) -> bool:
    """
    Контейнер иллюстрации в тексте статьи:
    - <figure typeof="mw:File..."> - актуальная разметка MediaWiki;
    - div.thumb - старая разметка (остаётся в галереях и блоках из
      нескольких картинок, например "thumb tmulti").
    """
    if tag.name == "figure":
        return (tag.get("typeof") or "").startswith("mw:File")
    return tag.name == "div" and "thumb" in (tag.get("class") or [])


def _is_skipped(container) -> bool:
    if container.find(class_="mw-kartographer-map"):
        return True
    for parent in container.parents:
        # Картинки в таблицах (включая инфобокс - у него свой путь ниже)
        # чаще всего значки; в навигации и служебных блоках - тоже.
        if parent.name == "table":
            return True
        if _SKIPPED_ANCESTOR_CLASSES & set(parent.get("class") or []):
            return True
    return False


def _body_caption(container):
    if container.name == "figure":
        return container.find("figcaption")
    gallery_box = container.find_parent(class_="gallerybox")
    if gallery_box is not None:
        return gallery_box.find(class_="gallerytext")
    return container.find(class_="thumbcaption")


def extract_images(html: str) -> list[Image]:
    """
    Извлекает изображения (§14 ТЗ) из тела статьи и из infobox
    (td.infobox-image).

    Тело статьи - в порядке документа: <figure typeof="mw:File...">
    с подписью в <figcaption> (актуальная разметка), div.thumb с
    подписью в .thumbcaption (старая разметка) и картинки галерей с
    подписью в .gallerytext. Пропускаются аудио и видео (нет <img>),
    карты mw-kartographer-map и картинки в таблицах, навигации и
    служебных блоках.
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    images: list[Image] = []
    seen: set[str] = set()

    containers: list[tuple[str, object]] = [
        ("body", container)
        for container in soup.find_all(_is_body_container)
        if not _is_skipped(container)
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
            caption_tag = _body_caption(container)
            if caption_tag:
                caption = _caption_text(caption_tag) or None
        else:  # infobox: подпись, если есть, в следующей строке таблицы
            row = container.find_parent("tr")
            next_row = row.find_next_sibling("tr") if row else None
            if next_row:
                caption_cell = next_row.find(class_="infobox-caption")
                if caption_cell:
                    caption = _caption_text(caption_cell) or None

        dedup_key = _file_title(container) or thumbnail_url
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        images.append(
            Image(url=url, thumbnail_url=thumbnail_url, caption=caption, alt=alt)
        )

    return images