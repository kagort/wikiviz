"""
Отбор надёжных данных (docs/SELECTION_TZ.md, утверждено владельцем 18.10).

Принцип: лучше не показать, чем показать мусор. Extractors честно
извлекают всё; этот слой решает, что из извлечённого показывать, и для
каждого отброшенного значения сохраняет код правила и причину.

Каждое правило - чистая функция над NormalizedArticleModel; правила
применяются по порядку внутри типа данных, первое сработавшее даёт
причину. Пороги собраны в SelectionConfig: значения правил «под
вопросом» - начальные, подбираются по разметке владельца (сессия 4).
"""
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

from app.models import (
    BlockType,
    Event,
    Image,
    NormalizedArticleModel,
    NumericValue,
    RejectedValue,
    SelectionResult,
    SourceType,
    Table,
)

_GROUP_SEPARATOR = " — "
_THUMB_WIDTH_RE = re.compile(r"/(\d+)px-")
_CODE_LABEL_RE = re.compile(
    r"calling code|telephone|phone code|time zone|utc|iso 3166|internet tld|tld|postal code|"
    r"телефонный код|часовой пояс|почтов|iso|код",
    re.IGNORECASE,
)
# \s - и неразрывный пробел: в разметке Wikipedia "Preceded&nbsp;by".
_NAVIGATION_RE = re.compile(r"Preceded\s+by|Succeeded\s+by|Предшественник|Преемник")
_LINK_TEXT_RE = re.compile(r"^(?:(?:Подробнее|More|See also|См\. также)[\s,]*)+$", re.IGNORECASE)


@dataclass(frozen=True)
class SelectionConfig:
    # Даты (Timeline)
    dense_section_dates: int = 10   # EV-DENSE: столько дат из абзацев одного раздела - перечень
    min_events: int = 2             # EV-MIN
    max_events: Optional[int] = None  # EV-MAX: под вопросом, по умолчанию выключено
    # Числа (StatisticsChart)
    units: frozenset = frozenset({
        "%", "km²", "км²", "km2", "/km²", "чел.", "чел./км²", "m", "м", "km", "км",
        "ft", "mi", "долл.", "$", "€", "кг", "kg", "°C", "мм", "mm",
    })
    min_group_size: int = 3         # NUM-GROUP
    # Таблицы
    min_table_rows: int = 2         # TBL-EMPTY
    min_table_columns: int = 2      # TBL-EMPTY
    misaligned_share: float = 0.3   # TBL-SHAPE
    blank_share: float = 0.3        # TBL-BLANK
    prose_cell_length: Optional[int] = None  # TBL-PROSE: под вопросом, выключено (таблица Python)
    max_tables: Optional[int] = None         # TBL-MAX: под вопросом, выключено
    # Инфобокс
    max_infobox_value: int = 200    # IB-LONG
    # Изображения
    min_thumb_width: int = 100      # IMG-ICON
    max_images: Optional[int] = 12  # IMG-MAX: под вопросом, начальное значение


DEFAULT_CONFIG = SelectionConfig()


class _Rejections:
    def __init__(self):
        self.items: list[RejectedValue] = []

    def add(self, kind: str, ref: str, preview: str, rule: str, reason: str) -> None:
        self.items.append(RejectedValue(kind=kind, ref=ref, preview=preview[:120], rule=rule, reason=reason))


# --- Даты ---------------------------------------------------------------------


def _event_preview(event: Event) -> str:
    return f"{event.date} «{event.title}»"


def _event_rule(event: Event) -> Optional[tuple[str, str]]:
    context = event.context
    if context is not None and context.service_section:
        return "EV-SERVICE", "дата из служебного раздела"
    if event.source == SourceType.ARTICLE_TEXT and context is not None and context.block == BlockType.LIST_ITEM:
        return "EV-LIST", "дата из пункта списка, а не из рассказа"
    return None


def select_events(events: list[Event], config: SelectionConfig, rejected: _Rejections) -> list[Event]:
    kept: list[Event] = []
    for event in events:
        rule = _event_rule(event)
        if rule:
            rejected.add("event", event.id, _event_preview(event), *rule)
        else:
            kept.append(event)

    # EV-DENSE: раздел, давший много дат из текста, - перечень, а не рассказ.
    per_section = Counter(
        tuple(e.context.section_path) for e in kept
        if e.source == SourceType.ARTICLE_TEXT and e.context is not None
    )
    dense = {path for path, count in per_section.items() if count >= config.dense_section_dates}
    remaining: list[Event] = []
    for event in kept:
        if (event.source == SourceType.ARTICLE_TEXT and event.context is not None
                and tuple(event.context.section_path) in dense):
            rejected.add("event", event.id, _event_preview(event), "EV-DENSE",
                         f"раздел даёт {config.dense_section_dates} и больше дат - похоже на перечень")
        else:
            remaining.append(event)

    # EV-DUP: одна дата - один раз; инфобокс важнее текста, ранний раздел - позднего.
    infobox_dates = {e.date for e in remaining if e.source == SourceType.INFOBOX}
    seen: set[str] = set()
    unique: list[Event] = []
    for event in remaining:
        duplicate = (event.source != SourceType.INFOBOX and event.date in infobox_dates) or (
            event.source != SourceType.INFOBOX and event.date in seen)
        if duplicate:
            rejected.add("event", event.id, _event_preview(event), "EV-DUP", "эта дата уже показана")
            continue
        if event.source != SourceType.INFOBOX:
            seen.add(event.date)
        unique.append(event)

    # EV-MAX (выключено по умолчанию): приоритет инфобоксу, затем тексту по порядку.
    if config.max_events is not None and len(unique) > config.max_events:
        ordered = sorted(range(len(unique)), key=lambda i: (unique[i].source != SourceType.INFOBOX, i))
        keep_indexes = set(ordered[: config.max_events])
        for i, event in enumerate(unique):
            if i not in keep_indexes:
                rejected.add("event", event.id, _event_preview(event), "EV-MAX",
                             f"на шкале не больше {config.max_events} событий")
        unique = [e for i, e in enumerate(unique) if i in keep_indexes]

    # EV-MIN: одна дата - ещё не хронология.
    if len(unique) < config.min_events:
        for event in unique:
            rejected.add("event", event.id, _event_preview(event), "EV-MIN",
                         f"после отбора меньше {config.min_events} событий - шкала не нужна")
        return []
    return unique


# --- Числа --------------------------------------------------------------------


def _number_preview(number: NumericValue) -> str:
    return f"{number.label} = {number.value:g} {number.unit or ''}".strip()


def _group_of(number: NumericValue) -> Optional[str]:
    index = number.label.find(_GROUP_SEPARATOR)
    return number.label[:index] if index > 0 else None


def select_numbers(numbers: list[NumericValue], config: SelectionConfig, rejected: _Rejections) -> list[NumericValue]:
    kept: list[tuple[int, NumericValue]] = []
    for index, number in enumerate(numbers):
        label_tail = number.label.split(_GROUP_SEPARATOR)[-1]
        if _CODE_LABEL_RE.search(label_tail):
            rule = ("NUM-CODE", "код или часовой пояс, а не величина")
        elif number.unit not in config.units:
            rule = ("NUM-UNIT", "нет распознанной единицы измерения")
        elif number.unit == "%" and not 0 <= number.value <= 100:
            rule = ("NUM-RANGE", "процент вне диапазона 0–100")
        elif number.value < 0:
            rule = ("NUM-RANGE", "отрицательная величина")
        else:
            kept.append((index, number))
            continue
        rejected.add("number", str(index), _number_preview(number), *rule)

    # NUM-GROUP: на диаграмму - группа с общим началом подписи и одной единицей.
    groups: dict[tuple, list[tuple[int, NumericValue]]] = defaultdict(list)
    for index, number in kept:
        groups[(_group_of(number), number.unit)].append((index, number))
    result: list[NumericValue] = []
    for index, number in kept:
        group = groups[(_group_of(number), number.unit)]
        if _group_of(number) is None or len(group) < config.min_group_size:
            rejected.add("number", str(index), _number_preview(number), "NUM-GROUP",
                         f"нет группы из {config.min_group_size} и больше значений с одной единицей")
        else:
            result.append(number)
    return result


# --- Таблицы ------------------------------------------------------------------


def _table_rule(table: Table, config: SelectionConfig) -> Optional[tuple[str, str]]:
    rows, columns = table.rows, table.columns
    cells = [cell for row in rows for cell in row]
    if any(_NAVIGATION_RE.search(text) for text in cells + columns):
        return "TBL-NAV", "таблица-навигация (кто был до и после)"
    if len(rows) < config.min_table_rows or len(columns) < config.min_table_columns:
        return "TBL-EMPTY", "меньше двух строк или колонок"
    if sum(len(row) != len(columns) for row in rows) / len(rows) > config.misaligned_share:
        return "TBL-SHAPE", "строки не совпадают с шапкой - похоже на таблицу вёрстки"
    if cells and sum(not c.strip() for c in cells) / len(cells) > config.blank_share:
        return "TBL-BLANK", "слишком много пустых ячеек"
    if config.prose_cell_length is not None and any(len(c) > config.prose_cell_length for c in cells):
        return "TBL-PROSE", "ячейка-абзац вместо данных"
    return None


def select_tables(tables: list[Table], config: SelectionConfig, rejected: _Rejections) -> list[Table]:
    kept: list[Table] = []
    for table in tables:
        rule = _table_rule(table, config)
        if rule:
            rejected.add("table", table.id, table.title or (" | ".join(table.columns[:3])), *rule)
        else:
            kept.append(table)
    if config.max_tables is not None and len(kept) > config.max_tables:
        ranked = sorted(kept, key=lambda t: (t.title is None, -len(t.rows)))
        allowed = {t.id for t in ranked[: config.max_tables]}
        for table in kept:
            if table.id not in allowed:
                rejected.add("table", table.id, table.title or "", "TBL-MAX",
                             f"не больше {config.max_tables} таблиц на статью")
        kept = [t for t in kept if t.id in allowed]
    return kept


# --- Инфобокс -----------------------------------------------------------------


def select_infobox(infobox: dict, config: SelectionConfig, rejected: _Rejections) -> dict:
    kept = {}
    for key, item in infobox.items():
        preview = f"{item.label}: {item.value}"
        if len(item.value) > config.max_infobox_value:
            rejected.add("infobox_field", key, preview, "IB-LONG",
                         f"значение длиннее {config.max_infobox_value} символов")
        elif _LINK_TEXT_RE.match(item.value):
            rejected.add("infobox_field", key, preview, "IB-LINKTEXT", "вместо значения - текст служебных ссылок")
        else:
            kept[key] = item
    return kept


# --- Изображения --------------------------------------------------------------


def _image_preview(image: Image) -> str:
    return image.caption or image.url.rsplit("/", 1)[-1].split("?")[0]


def select_images(images: list[Image], config: SelectionConfig, rejected: _Rejections) -> list[Image]:
    kept: list[tuple[int, Image]] = []
    for index, image in enumerate(images):
        context = image.context
        block = context.block if context is not None else None
        match = _THUMB_WIDTH_RE.search(image.thumbnail_url or "")
        if context is not None and context.service_section:
            rule = ("IMG-SERVICE", "изображение из служебного раздела")
        elif not image.caption and block != BlockType.INFOBOX:
            rule = ("IMG-NOCAP", "нет подписи")
        elif match and int(match.group(1)) < config.min_thumb_width:
            rule = ("IMG-ICON", "значок или очень мелкое изображение")
        else:
            kept.append((index, image))
            continue
        rejected.add("image", str(index), _image_preview(image), *rule)

    if config.max_images is not None and len(kept) > config.max_images:
        # Приоритет: изображение инфобокса, иллюстрации в порядке статьи, галереи последними.
        def priority(item):
            index, image = item
            block = image.context.block if image.context is not None else None
            rank = {BlockType.INFOBOX: 0, BlockType.FIGURE: 1}.get(block, 2)
            return (rank, index)

        allowed = {index for index, _ in sorted(kept, key=priority)[: config.max_images]}
        for index, image in kept:
            if index not in allowed:
                rejected.add("image", str(index), _image_preview(image), "IMG-MAX",
                             f"не больше {config.max_images} изображений на статью")
        kept = [(i, img) for i, img in kept if i in allowed]
    return [image for _, image in kept]


# --- Координаты ---------------------------------------------------------------


def select_locations(locations: list, rejected: _Rejections) -> list:
    kept = []
    for index, location in enumerate(locations):
        if -90 <= location.latitude <= 90 and -180 <= location.longitude <= 180:
            kept.append(location)
        else:
            rejected.add("location", str(index), f"{location.latitude}, {location.longitude}",
                         "LOC-RANGE", "координаты вне допустимого диапазона")
    return kept


# --- Вся статья ---------------------------------------------------------------


def select_reliable(model: NormalizedArticleModel, config: SelectionConfig = DEFAULT_CONFIG) -> SelectionResult:
    """Отбирает надёжные данные статьи; разделы, статья и заглушки не меняются."""
    rejected = _Rejections()
    selected = model.model_copy(update={
        "events": select_events(model.events, config, rejected),
        "numbers": select_numbers(model.numbers, config, rejected),
        "tables": select_tables(model.tables, config, rejected),
        "infobox": select_infobox(model.infobox, config, rejected),
        "images": select_images(model.images, config, rejected),
        "locations": select_locations(model.locations, rejected),
    })
    return SelectionResult(selected=selected, rejected=rejected.items)
