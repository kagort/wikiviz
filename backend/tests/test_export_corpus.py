"""
Выгрузка корпуса проверки устойчивости (план, сессия 2).

Сеть не используется: вместо WikipediaClient подставляется заглушка.
"""
import json

import scripts.export_corpus as export_corpus_module
from app.extractors.article_normalizer import normalize_article
from app.wikipedia.models import RawArticle
from scripts.export_corpus import export_corpus
from scripts.export_fixtures import ManifestEntry


class FakeClient:
    def __init__(self, latest_revision=777, fail_on=()):
        self.latest_revision = latest_revision
        self.fail_on = set(fail_on)
        self.calls = []

    def fetch_article(self, url, revision_id=None):
        self.calls.append((url, revision_id))
        if url in self.fail_on:
            raise RuntimeError("network down")
        revision = revision_id if revision_id is not None else self.latest_revision
        return RawArticle(
            page_id=1, title="T", language="en", url=url, revision_id=revision,
            html="<h2>A</h2><p>x</p>",
        )


def entry(name, revision=1, kind="person"):
    return ManifestEntry(url=f"https://en.wikipedia.org/wiki/{name}", revision=revision,
                         file=f"{name.lower()}.json", kind=kind)


def test_failure_on_one_article_does_not_stop_the_others(tmp_path, monkeypatch):
    entries = [entry("A"), entry("B"), entry("C")]
    client = FakeClient(fail_on={entries[0].url})

    def normalize_failing_on_b(raw):
        if raw.url == entries[1].url:
            raise ValueError("bad table")
        return normalize_article(raw)

    monkeypatch.setattr(export_corpus_module, "normalize_article", normalize_failing_on_b)

    result, errors = export_corpus(entries, client, tmp_path)

    assert [(e["file"], e["stage"]) for e in errors] == [("a.json", "fetch"), ("b.json", "normalize")]
    assert errors[0]["error"] == "RuntimeError: network down"
    assert errors[1]["error"] == "ValueError: bad table"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["c.json"]
    assert json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))["article"]["title"] == "T"
    assert result == entries


def test_unpinned_entry_is_reported_and_not_fetched_without_pin_missing(tmp_path):
    entries = [entry("A", revision=None)]
    client = FakeClient()

    result, errors = export_corpus(entries, client, tmp_path)

    assert client.calls == []
    assert [e["stage"] for e in errors] == ["unpinned"]
    assert result == entries


def test_pin_missing_pins_only_unpinned_entries(tmp_path):
    entries = [entry("A", revision=5), entry("B", revision=None)]
    client = FakeClient(latest_revision=777)

    result, errors = export_corpus(entries, client, tmp_path, pin_missing=True)

    assert errors == []
    assert client.calls == [(entries[0].url, 5), (entries[1].url, None)]
    assert [e.revision for e in result] == [5, 777]
    assert result[1].kind == "person"
