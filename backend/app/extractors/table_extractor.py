from bs4 import BeautifulSoup

from app.models import Table


def extract_tables(html: str) -> list[Table]:
    """
    Извлекает информационные таблицы Wikipedia (§12 ТЗ).

    Ищет только <table class="wikitable"> - так MediaWiki размечает
    "настоящие" таблицы с данными, в отличие от infobox и navbox,
    которые тоже являются <table>, но обрабатываются другими extractors
    (или не обрабатываются вовсе).
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    raw_tables = soup.find_all("table", class_="wikitable")

    tables = []
    for index, raw_table in enumerate(raw_tables):
        caption_tag = raw_table.find("caption")
        title = caption_tag.get_text(strip=True) if caption_tag else None

        all_rows = raw_table.find_all("tr")
        if not all_rows:
            continue

        header_cells = all_rows[0].find_all(["th", "td"])
        columns = [cell.get_text(strip=True) for cell in header_cells]

        rows = []
        for tr in all_rows[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row = [cell.get_text(strip=True) for cell in cells]
            rows.append(row)

        tables.append(
            Table(
                id=f"table-{index}",
                title=title,
                columns=columns,
                rows=rows,
            )
        )

    return tables
