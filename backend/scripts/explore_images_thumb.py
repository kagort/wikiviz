"""
Уточняющая разведка: структура ОБЫЧНОЙ иллюстрации в теле статьи
(div.thumb) - не infobox, не карта.

Запуск:
    python -m scripts.explore_images_thumb
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

URL = "https://en.wikipedia.org/wiki/Mount_Everest"


def main() -> None:
    client = WikipediaClient()
    raw = client.fetch_article(URL)
    soup = BeautifulSoup(raw.html, "html.parser")

    # div.thumb, исключая карты (mw-kartographer)
    thumbs = [
        div for div in soup.find_all("div", class_="thumb")
        if not div.find(class_="mw-kartographer-map")
    ]

    print(f"div.thumb (без карт): {len(thumbs)}")
    print()

    for thumb in thumbs[:3]:
        img = thumb.find("img")
        caption = thumb.find(class_="thumbcaption")

        print(f"src: {img.get('src') if img else None}")
        print(f"alt: {img.get('alt') if img else None!r}")
        print(f"width: {img.get('width') if img else None}")
        print(f"thumbcaption raw text: {caption.get_text(strip=True) if caption else None!r}")
        # thumbcaption часто содержит служебную ссылку magnify/увеличение -
        # посмотрим на полную HTML-структуру caption, чтобы понять, что убирать
        if caption:
            print(f"thumbcaption html (первые 300 симв.): {str(caption)[:300]}")
        print()

    # Отдельно посмотрим на infobox-изображение: есть ли у него подпись
    # (обычно в отдельной строке таблицы после infobox-image)
    print("--- infobox-image caption? ---")
    infobox_img_cell = soup.find("td", class_="infobox-image")
    if infobox_img_cell:
        next_row = infobox_img_cell.find_parent("tr").find_next_sibling("tr")
        if next_row:
            caption_cell = next_row.find(class_="infobox-caption")
            print(f"infobox-caption: {caption_cell.get_text(strip=True) if caption_cell else None!r}")
        else:
            print("следующей строки после infobox-image нет")


if __name__ == "__main__":
    main()