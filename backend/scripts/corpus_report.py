"""
Офлайн-анализ корпуса проверки устойчивости (план, сессия 2).

Читает сохранённые результаты нормализации (tests/corpus/articles/*.json)
и печатает в Markdown:
  - по каждой статье - сколько данных каждого типа извлечено;
  - признаки шума по типам данных с примерами.
Сеть не нужна, результат воспроизводим. Пороги признаков - для
разведки, это ещё не правила отбора (они - предмет сессии 3).

Запуск (из папки backend):
    python -m scripts.corpus_report > ../отчёт.md
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from scripts.export_corpus import ARTICLES_DIR, ERRORS_PATH, MANIFEST_PATH
from scripts.export_fixtures import load_manifest

LONG_CELL = 300
LONG_INFOBOX_VALUE = 200
RECENT_YEAR = 2000
EXAMPLES = 4

_SUCCESSION_RE = re.compile(r"Preceded by|Succeeded by|Предшественник|Преемник")
_TEMPLATE_ERROR_RE = re.compile(r"Lua error|Script error|Ошибка Lua|Ошибка скрипта")
_YEAR_UNIT_RE = re.compile(r"^(year|years|BC|BCE|до|н\.|г\.|год|года)$")
_CODE_LABEL_RE = re.compile(r"code|код|ISO|time zone|часовой|UTC|TLD|телефон", re.IGNORECASE)
_THUMB_WIDTH_RE = re.compile(r"/(\d+)px-")
_FLAG_RE = re.compile(r"Flag_of|Coat_of_arms|Флаг|Герб")


class Signals:
    """Счётчик признаков шума с несколькими примерами на признак."""

    def __init__(self):
        self.counts: Counter = Counter()
        self.examples: dict[str, list[str]] = defaultdict(list)

    def add(self, name: str, example: str) -> None:
        self.counts[name] += 1
        if len(self.examples[name]) < EXAMPLES:
            self.examples[name].append(example)


def _flat_sections(sections) -> int:
    return sum(1 + _flat_sections(s["children"]) for s in sections)


def _year(date: str) -> int:
    return int(date[:5]) if date.startswith("-") else int(date[:4])


def analyze_article(name: str, data: dict, signals: dict[str, Signals]) -> None:
    for table in data["tables"]:
        s = signals["tables"]
        s.counts["всего таблиц"] += 1
        title = table["title"] or "(без названия)"
        rows, columns = table["rows"], table["columns"]
        cells = [cell for row in rows for cell in row]
        where = f"{name}: {title[:50]}"
        if not table["title"]:
            s.counts["без названия"] += 1
        if len(rows) <= 1:
            s.add("не больше одной строки данных", where)
        if len(columns) <= 1:
            s.add("одна колонка", where)
        if rows and sum(len(r) != len(columns) for r in rows) / len(rows) > 0.3:
            s.add("строки не совпадают с колонками (>30% строк)", where)
        if cells and sum(not c.strip() for c in cells) / len(cells) > 0.3:
            s.add("больше 30% пустых ячеек", where)
        if any(len(c) > LONG_CELL for c in cells):
            s.add(f"ячейка длиннее {LONG_CELL} символов", where)
        if any(_SUCCESSION_RE.search(c) for c in cells + columns):
            s.add("таблица-навигация (Preceded by / Succeeded by)", where)
        if any(_TEMPLATE_ERROR_RE.search(c) for c in cells):
            s.add("текст ошибки шаблона", where)

    s = signals["infobox"]
    if not data["infobox"]:
        s.add("статья без инфобокса", name)
    for field in data["infobox"].values():
        s.counts["всего полей"] += 1
        if len(field["value"]) > LONG_INFOBOX_VALUE:
            s.add(f"значение длиннее {LONG_INFOBOX_VALUE} символов",
                  f"{name}: {field['label'][:40]} ({len(field['value'])})")
        if len(field["label"]) > 40:
            s.add("подпись длиннее 40 символов", f"{name}: {field['label'][:60]}")

    s = signals["events"]
    text_events = [e for e in data["events"] if e["source"] == "article_text"]
    s.counts["всего событий"] += len(data["events"])
    s.counts["из текста статьи"] += len(text_events)
    by_section = Counter(e["title"] for e in text_events)
    for section, count in by_section.items():
        if count >= 10:
            s.add("раздел, давший 10 и больше дат", f"{name}: «{section[:40]}» — {count}")
    by_date = Counter(e["date"] for e in text_events)
    for date, count in by_date.items():
        if count > 1:
            s.add("одна дата в нескольких разделах", f"{name}: {date} ×{count}")
    for event in text_events:
        if _year(event["date"]) >= RECENT_YEAR:
            s.add(f"дата из текста не раньше {RECENT_YEAR} года", f"{name}: {event['date']} «{event['title'][:30]}»")
    if len(data["events"]) < 2:
        s.add("меньше двух событий (шкала не покажется)", name)

    s = signals["numbers"]
    for number in data["numbers"]:
        s.counts["всего чисел"] += 1
        unit, label = number["unit"], number["label"]
        where = f"{name}: {label[:45]} = {number['value']:g} {unit or ''}".rstrip()
        if unit is None:
            s.add("без единицы измерения", where)
        elif _YEAR_UNIT_RE.match(unit):
            s.add("на самом деле год", where)
        elif unit == "%" and not 0 <= number["value"] <= 100:
            s.add("процент вне 0..100", where)
        elif unit == "%":
            s.counts["в процентах"] += 1
        if _CODE_LABEL_RE.search(label):
            s.add("код или часовой пояс", where)

    s = signals["images"]
    for image in data["images"]:
        s.counts["всего изображений"] += 1
        file_name = image["url"].rsplit("/", 1)[-1].split("?")[0]
        if not image["caption"]:
            s.add("без подписи", f"{name}: {file_name[:60]}")
        match = _THUMB_WIDTH_RE.search(image["thumbnail_url"] or "")
        if match and int(match.group(1)) < 100:
            s.add("превью уже 100px", f"{name}: {file_name[:60]}")
        if _FLAG_RE.search(image["url"]):
            s.add("флаг или герб", f"{name}: {file_name[:60]}")

    s = signals["locations"]
    s.counts["всего точек"] += len(data["locations"])
    if not data["locations"]:
        s.counts["статей без координат"] += 1


def main() -> None:
    entries = load_manifest(MANIFEST_PATH)
    errors = json.loads(Path(ERRORS_PATH).read_text(encoding="utf-8"))
    signals = {key: Signals() for key in ("tables", "infobox", "events", "numbers", "images", "locations")}

    print("## Статьи корпуса\n")
    print("| Файл | Тип | Разделы | Таблицы | Поля инфобокса | События (инфобокс / текст) | Числа | Изображения | Координаты |")
    print("|---|---|---|---|---|---|---|---|---|")
    for entry in entries:
        path = ARTICLES_DIR / entry.file
        if not path.exists():
            print(f"| {entry.file} | {entry.kind} | нет результата | | | | | | |")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        events = data["events"]
        from_infobox = sum(e["source"] == "infobox" for e in events)
        print(f"| {entry.file[:-5]} | {entry.kind} | {_flat_sections(data['sections'])} | {len(data['tables'])} "
              f"| {len(data['infobox'])} | {from_infobox} / {len(events) - from_infobox} | {len(data['numbers'])} "
              f"| {len(data['images'])} | {len(data['locations'])} |")
        analyze_article(entry.file[:-5], data, signals)

    print(f"\nОшибок загрузки и нормализации: {len(errors)}.")
    for error in errors:
        print(f"- {error['file']} ({error['stage']}): {error['error']}")

    titles = {"tables": "Таблицы", "infobox": "Инфобокс", "events": "Даты",
              "numbers": "Числа", "images": "Изображения", "locations": "Координаты"}
    for key, title in titles.items():
        s = signals[key]
        print(f"\n## {title}\n")
        for name, count in s.counts.most_common():
            print(f"- **{name}**: {count}")
            for example in s.examples.get(name, []):
                print(f"  - {example}")


if __name__ == "__main__":
    main()
