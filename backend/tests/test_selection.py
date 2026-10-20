"""
Отбор надёжных данных (docs/SELECTION_TZ.md): правила по типам данных.

Синтетические примеры повторяют находки корпуса; в конце - проверки на
настоящих статьях корпуса и фикстур (без сети, по сохранённым JSON).
"""
from dataclasses import replace
from pathlib import Path

from app.models import (
    BlockType,
    DatePrecision,
    Event,
    Image,
    InfoboxField,
    NormalizedArticleModel,
    NumericValue,
    SourceType,
    Table,
    ValueContext,
)
from app.models.article import Article
from app.transformers.selection import DEFAULT_CONFIG, select_reliable

# Правила для дат из текста (EV-LIST, EV-DENSE, ...) проверяются в режиме,
# где такие даты включены; по умолчанию они отсекаются (EV-TEXT, решение
# владельца 20.10 по разметке).
TEXT_ON = replace(DEFAULT_CONFIG, text_events=True)

CORPUS = Path(__file__).parent / "corpus" / "articles"
FIXTURES = Path(__file__).parent.parent.parent / "frontend" / "tests" / "fixtures" / "real"


def model(**data) -> NormalizedArticleModel:
    article = Article(id=1, title="T", language="en", url="https://en.wikipedia.org/wiki/T")
    return NormalizedArticleModel(article=article, **data)


def ctx(block=BlockType.PARAGRAPH, path=("History",), service=False):
    return ValueContext(block=block, section_path=list(path), service_section=service)


def text_event(i, date, block=BlockType.PARAGRAPH, path=("History",), service=False):
    return Event(id=f"text-event-{i}", date=date, date_precision=DatePrecision.DAY, title=path[-1] if path else "Introduction",
                 source=SourceType.ARTICLE_TEXT, confidence=0.6, context=ctx(block, path, service))


def infobox_event(i, date):
    return Event(id=f"event-{i}", date=date, date_precision=DatePrecision.DAY, title="Born",
                 source=SourceType.INFOBOX, context=ctx(BlockType.INFOBOX, ()))


def rules(result):
    return [(r.kind, r.rule) for r in result.rejected]


# --- Даты ---------------------------------------------------------------------


def test_list_item_dates_are_rejected_paragraph_dates_kept():
    result = select_reliable(model(events=[
        text_event(0, "1961-04-12"),
        text_event(1, "1961-04-14", block=BlockType.LIST_ITEM, path=("Awards",)),
        text_event(2, "1968-03-27"),
    ]), TEXT_ON)

    assert [e.date for e in result.selected.events] == ["1961-04-12", "1968-03-27"]
    assert rules(result) == [("event", "EV-LIST")]
    assert result.rejected[0].reason == "дата из пункта списка, а не из рассказа"


def test_dense_section_is_treated_as_enumeration():
    events = [text_event(i, f"20{i:02d}-01-01", path=("Scientific",)) for i in range(10)]
    events += [text_event(10, "1879-03-14", path=("Life",)), text_event(11, "1955-04-18", path=("Life",))]

    result = select_reliable(model(events=events), TEXT_ON)

    assert [e.date for e in result.selected.events] == ["1879-03-14", "1955-04-18"]
    assert {r.rule for r in result.rejected} == {"EV-DENSE"}


def test_same_date_is_shown_once_and_infobox_wins():
    result = select_reliable(model(events=[
        infobox_event(0, "1879-03-14"),
        text_event(1, "1879-03-14", path=()),
        text_event(2, "1905-06-30", path=("Career",)),
        text_event(3, "1905-06-30", path=("Legacy",)),
    ]), TEXT_ON)

    assert [(e.source.value, e.date) for e in result.selected.events] == [
        ("infobox", "1879-03-14"), ("article_text", "1905-06-30")]
    assert [r.rule for r in result.rejected] == ["EV-DUP", "EV-DUP"]


def test_single_event_after_selection_gives_no_timeline():
    result = select_reliable(model(events=[
        text_event(0, "1961-04-12"),
        text_event(1, "1961-04-14", block=BlockType.LIST_ITEM),
    ]), TEXT_ON)

    assert result.selected.events == []
    assert [r.rule for r in result.rejected] == ["EV-LIST", "EV-MIN"]


def test_service_section_values_are_rejected():
    result = select_reliable(model(events=[
        text_event(0, "2015-05-21", path=("Литература", "Статьи"), service=True),
        text_event(1, "1961-04-12"), text_event(2, "1968-03-27"),
    ]), TEXT_ON)

    assert [r.rule for r in result.rejected] == ["EV-SERVICE"]


def test_max_events_is_off_by_default_and_prefers_infobox_when_on():
    events = [infobox_event(0, "1879-03-14")] + [text_event(i, f"19{i:02d}-01-01", path=(f"S{i}",)) for i in range(1, 6)]

    assert len(select_reliable(model(events=events), TEXT_ON).selected.events) == 6

    limited = select_reliable(model(events=events), replace(TEXT_ON, max_events=3))
    assert [e.date for e in limited.selected.events] == ["1879-03-14", "1901-01-01", "1902-01-01"]


# --- Числа --------------------------------------------------------------------


def number(label, value, unit):
    return NumericValue(label=label, value=value, unit=unit, source=SourceType.INFOBOX)


def test_numbers_need_known_unit_and_a_group():
    result = select_reliable(model(numbers=[
        number("Religion — Christianity", 48, "%"),
        number("Religion — Islam", 7, "%"),
        number("Religion — Judaism", 1, "%"),
        number("Citizenship", 1896, "year"),          # год, а не величина
        number("Gini (2025)", 30.4, "medium"),        # слово вместо единицы
        number("Area — Total", 632702.3, "km²"),      # единица есть, но группа из одного
    ]))

    assert [n.label for n in result.selected.numbers] == [
        "Religion — Christianity", "Religion — Islam", "Religion — Judaism"]
    assert [r.rule for r in result.rejected] == ["NUM-UNIT", "NUM-UNIT", "NUM-GROUP"]


def test_codes_and_bad_percentages_are_rejected():
    result = select_reliable(model(numbers=[
        number("GDP (nominal) — Calling code", 33, "%"),
        number("Share — A", 140, "%"),
    ]))

    assert [r.rule for r in result.rejected] == ["NUM-CODE", "NUM-RANGE"]


# --- Таблицы ------------------------------------------------------------------


def table(i, columns, rows, title=None):
    return Table(id=f"table-{i}", title=title, columns=columns, rows=rows)


def test_table_shape_rules():
    good = table(0, ["Year", "Population"], [["1990", "10"], ["2000", "12"]], "Population")
    result = select_reliable(model(tables=[
        good,
        table(1, ["Political offices", "B", "C"], [["Preceded\xa0by A", "Roman consul", "Succeeded by B"], ["x", "y", "z"]]),
        table(2, ["Only header", "B"], [["1", "2"]]),
        table(3, ["A"], [["1"], ["2"]]),
        table(4, ["A", "B", "C"], [["1", "2"], ["3", "4"], ["5", "6", "7"]]),
        table(5, ["A", "B"], [["", ""], ["1", ""]]),
    ]))

    assert [t.id for t in result.selected.tables] == ["table-0"]
    assert [r.rule for r in result.rejected] == ["TBL-NAV", "TBL-EMPTY", "TBL-EMPTY", "TBL-SHAPE", "TBL-BLANK"]


# --- Инфобокс -----------------------------------------------------------------


def field(key, label, value):
    return InfoboxField(key=key, label=label, value=value)


def test_long_and_link_text_infobox_values_are_rejected():
    result = select_reliable(model(infobox={
        "born": field("born", "Born", "14 March 1879"),
        "notable_ideas": field("notable_ideas", "Notable ideas", "x" * 739),
        "потери": field("потери", "Потери", "Подробнее, Подробнее"),
    }))

    assert list(result.selected.infobox) == ["born"]
    assert [r.rule for r in result.rejected] == ["IB-LONG", "IB-LINKTEXT"]


def test_identifier_fields_are_rejected():
    result = select_reliable(model(infobox={
        "website": field("website", "Website", "alberteinstein.com"),
        "unii": field("unii", "UNII", "059QF0KO0R"),
        "телефонный_код": field("телефонный_код", "Телефонный код", "+49"),
        "odor": field("odor", "Odor", "Odorless"),
    }))

    assert list(result.selected.infobox) == ["odor"]
    assert [r.rule for r in result.rejected] == ["IB-ID", "IB-ID", "IB-ID"]


def test_taxonomy_rows_are_rejected_only_as_a_block():
    taxobox = {k: field(k, f"{k.title()}:", v) for k, v in
               [("kingdom", "Animalia"), ("phylum", "Chordata"), ("class", "Mammalia"), ("family", "Felidae")]}
    taxobox["conservation"] = field("conservation", "Conservation status", "Endangered")

    result = select_reliable(model(infobox=taxobox))

    assert list(result.selected.infobox) == ["conservation"]
    assert {r.rule for r in result.rejected} == {"IB-TAXO"}

    # Одиночное поле "Тип" (например, тип населённого пункта) - не классификация.
    single = select_reliable(model(infobox={"тип": field("тип", "Тип", "город")}))
    assert list(single.selected.infobox) == ["тип"]


def test_parent_row_without_own_value_is_rejected():
    result = select_reliable(model(infobox={
        "gdp_ppp": InfoboxField(key="gdp_ppp", label="GDP (PPP)", value="2026 estimate"),
        "gdp_ppp_total": InfoboxField(key="gdp_ppp_total", label="Total", group="GDP (PPP)", value="$4.734 trillion"),
        "government": InfoboxField(key="government", label="Government", value="Unitary republic"),
        "government_president": InfoboxField(key="government_president", label="President", group="Government",
                                             value="Emmanuel Macron"),
    }))

    assert list(result.selected.infobox) == ["gdp_ppp_total", "government", "government_president"]
    assert [r.rule for r in result.rejected] == ["IB-PARENT"]


# --- Изображения --------------------------------------------------------------


def image(name, caption, block=BlockType.FIGURE, width=250, service=False):
    return Image(url=f"https://x/1280px-{name}", thumbnail_url=f"https://x/{width}px-{name}", caption=caption,
                 context=ctx(block, ("History",), service))


def test_image_rules_and_infobox_image_without_caption_is_kept():
    result = select_reliable(model(images=[
        image("flag.png", None, block=BlockType.INFOBOX),
        image("photo.jpg", "A photo"),
        image("nocap.jpg", None),
        image("coin.jpg", "Coin", width=60),
        image("stamp.jpg", "Stamp", block=BlockType.GALLERY, service=True),
    ]))

    assert [i.url.rsplit("-", 1)[-1] for i in result.selected.images] == ["flag.png", "photo.jpg"]
    assert [r.rule for r in result.rejected] == ["IMG-NOCAP", "IMG-ICON", "IMG-SERVICE"]


def test_image_limit_keeps_infobox_then_figures_then_galleries():
    images = [image(f"g{i}.jpg", f"G{i}", block=BlockType.GALLERY) for i in range(3)]
    images += [image(f"f{i}.jpg", f"F{i}") for i in range(3)] + [image("ib.png", None, block=BlockType.INFOBOX)]

    result = select_reliable(model(images=images), replace(DEFAULT_CONFIG, max_images=4))

    # Отбрасываются галереи: приоритет у инфобокса и иллюстраций.
    assert sorted(i.caption or "infobox" for i in result.selected.images) == ["F0", "F1", "F2", "infobox"]
    assert {r.rule for r in result.rejected} == {"IMG-MAX"}


# --- Настоящие статьи ---------------------------------------------------------


def load(path: Path) -> NormalizedArticleModel:
    return NormalizedArticleModel.model_validate_json(path.read_text(encoding="utf-8"))


def test_gagarin_awards_list_does_not_reach_the_timeline():
    result = select_reliable(load(CORPUS / "gagarin-ru.json"), TEXT_ON)

    shown_sections = {tuple(e.context.section_path) for e in result.selected.events if e.context}
    assert not any(path and path[0] == "Почётные звания и награды" for path in shown_sections)
    assert any(r.rule == "EV-LIST" for r in result.rejected)


def test_france_keeps_religion_chart_and_drops_codes():
    result = select_reliable(load(FIXTURES / "france.json"))

    labels = [n.label for n in result.selected.numbers]
    assert any(label.startswith("Religion (2025) — ") for label in labels)
    assert not any("Calling code" in label or "Time zone" in label for label in labels)


def test_caesar_offices_navigation_table_is_rejected():
    result = select_reliable(load(FIXTURES / "julius-caesar.json"))

    assert any(r.rule == "TBL-NAV" for r in result.rejected)
    assert all(not any("Preceded by" in c for row in t.rows for c in row) for t in result.selected.tables)


def test_selection_never_fails_on_the_whole_corpus():
    for path in sorted(CORPUS.glob("*.json")):
        result = select_reliable(load(path))
        assert len(result.selected.events) != 1  # EV-MIN: либо пусто, либо хронология


def test_stored_selection_files_match_current_rules():
    # Результаты отбора рядом с фикстурами и корпусом (scripts.apply_selection)
    # должны соответствовать текущим правилам: иначе /dev/widgets и тесты
    # frontend показывают устаревший отбор. Исправление - перезапустить
    # python -m scripts.apply_selection.
    for source in (FIXTURES, CORPUS):
        for path in sorted(source.glob("*.json")):
            if path.name == "manifest.json":
                continue
            stored = (path.parent.parent / "selection" / path.name) if source == CORPUS else (path.parent / "selection" / path.name)
            expected = select_reliable(load(path)).model_dump_json(indent=2)
            assert stored.read_text(encoding="utf-8") == expected, f"{stored} устарел"
