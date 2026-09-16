"""
Уточняющая разведка: почему "Founded" (United Nations) и дата события
(Battle of Actium) не были найдены предыдущим скриптом.

Запуск:
    python -m scripts.explore_dates_edge_cases
"""

from bs4 import BeautifulSoup

from app.wikipedia.client import WikipediaClient

client = WikipediaClient()


def explore_un() -> None:
    print("=" * 70)
    print("UNITED NATIONS — ищем ВСЕ строки infobox целиком")
    print("=" * 70)

    raw = client.fetch_article("https://en.wikipedia.org/wiki/United_Nations")
    soup = BeautifulSoup(raw.html, "html.parser")

    rows = soup.find_all("tr")
    for row in rows[:25]:
        label_cell = row.find(class_="infobox-label")
        data_cell = row.find(class_="infobox-data")
        if label_cell or data_cell:
            label_text = label_cell.get_text(strip=True) if label_cell else None
            data_text = data_cell.get_text(strip=True) if data_cell else None
            print(f"  label={label_text!r}  data={data_text!r}")


def explore_actium() -> None:
    print()
    print("=" * 70)
    print("BATTLE OF ACTIUM — ищем инфобокс целиком и дату в тексте")
    print("=" * 70)

    raw = client.fetch_article("https://en.wikipedia.org/wiki/Battle_of_Actium")
    soup = BeautifulSoup(raw.html, "html.parser")

    infobox = soup.find("table", class_="infobox")
    if infobox is None:
        print("  infobox не найден вообще")
    else:
        rows = infobox.find_all("tr")
        for row in rows[:15]:
            print(f"  row text: {row.get_text(' ', strip=True)[:150]!r}")

    # Ищем BC/BCE прямо в тексте статьи
    print()
    print("  Поиск 'BC' в первых 500 символах текста статьи:")
    full_text = soup.get_text()
    idx = full_text.find("BC")
    print(f"  контекст: ...{full_text[max(0, idx-80):idx+20]}...")


if __name__ == "__main__":
    explore_un()
    explore_actium()