"""
Данные страницы разметки и подсчёт качества отбора (сессия 4, В5-В6).
Без сети: маленький корпус собирается во временной папке.
"""
import json

from app.models import Article, DatePrecision, Event, NormalizedArticleModel, SourceType
from app.transformers.selection import select_reliable
from scripts.build_review import article_values, build_review
from scripts.export_fixtures import ManifestEntry, save_manifest
from scripts.selection_quality import quality


def make_model(title, events):
    article = Article(id=1, title=title, language="en", url=f"https://en.wikipedia.org/wiki/{title}")
    return NormalizedArticleModel(article=article, events=events)


def event(i, date, title="Born", source=SourceType.INFOBOX):
    prefix = "event" if source == SourceType.INFOBOX else "text-event"
    return Event(id=f"{prefix}-{i}", date=date, date_precision=DatePrecision.DAY, title=title, source=source)


def write_corpus(tmp_path, articles):
    (tmp_path / "articles").mkdir()
    (tmp_path / "selection").mkdir()
    entries = []
    for file, kind, model in articles:
        (tmp_path / "articles" / file).write_text(model.model_dump_json(), encoding="utf-8")
        (tmp_path / "selection" / file).write_text(select_reliable(model).model_dump_json(), encoding="utf-8")
        entries.append(ManifestEntry(url=model.article.url, revision=1, file=file, kind=kind))
    save_manifest(tmp_path / "manifest.json", entries)


def test_values_carry_selection_status_and_content_keys():
    model = make_model("A", [
        event(0, "1900-01-01", "Born"),
        event(1, "1950-05-05", "Died"),
        event(2, "1920-01-01", "History", SourceType.ARTICLE_TEXT),
    ])

    values = article_values("a.json", model, select_reliable(model))

    assert [(v["key"], v["selected"], v["rule"]) for v in values] == [
        ("a.json|event|1900-01-01|Born|infobox", True, None),
        ("a.json|event|1950-05-05|Died|infobox", True, None),
        ("a.json|event|1920-01-01|History|article_text", False, "EV-TEXT"),
    ]


def test_sample_excludes_control_group_and_only_shown_values(tmp_path):
    write_corpus(tmp_path, [
        ("a.json", "person", make_model("A", [event(0, "1900-01-01"), event(1, "1950-05-05")])),
        ("r.json", "random", make_model("R", [event(0, "1800-01-01"), event(1, "1810-01-01")])),
    ])

    articles, sample = build_review(tmp_path)

    assert [a["file"] for a in articles] == ["a.json", "r.json"]
    assert {v["file"] for v in sample} == {"a.json"}
    assert all(v["selected"] for v in sample)


def test_quality_counts_precision_lost_ok_values_and_lost_golden():
    articles = [
        {"title": "A", "kind": "person", "values": [
            {"key": "k1", "kind": "event", "selected": True, "preview": "", "rule": None, "reason": None},
            {"key": "k2", "kind": "event", "selected": True, "preview": "", "rule": None, "reason": None},
            {"key": "k3", "kind": "event", "selected": False, "preview": "x", "rule": "EV-LIST", "reason": "r"},
        ]},
        {"title": "R", "kind": "random", "values": [
            {"key": "k4", "kind": "event", "selected": True, "preview": "", "rule": None, "reason": None},
        ]},
    ]
    labels = {"labels": {"k1": "ok", "k2": "junk", "k3": "ok", "k4": "ok"}, "golden": ["k3"]}

    result = quality(articles, labels)

    assert result["main"]["event"] == {"ok": 1, "junk": 1, "ok_rejected": 1}
    assert result["control"]["event"] == {"ok": 1, "junk": 0, "ok_rejected": 0}
    assert [v["key"] for v in result["golden_lost"]] == ["k3"]


def test_stored_review_files_match_current_selection():
    # Как и результаты отбора: после изменения правил нужно перезапустить
    # python -m scripts.apply_selection (он пересобирает и эти файлы).
    from scripts.build_review import REVIEW_DIR

    articles, sample = build_review()
    for name, data in (("articles.json", articles), ("sample.json", sample)):
        stored = (REVIEW_DIR / name).read_text(encoding="utf-8")
        assert stored == json.dumps(data, ensure_ascii=False, indent=1) + "\n", f"{name} устарел"
