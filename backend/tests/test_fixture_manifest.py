"""
Манифест фикстур и выгрузка по зафиксированной ревизии (Phase 6, этап 1).

Сеть не используется: вместо WikipediaClient подставляется заглушка.
"""
import json

import pytest

from app.wikipedia.models import RawArticle
from scripts.export_fixtures import (
    ManifestEntry,
    ManifestError,
    export_fixtures,
    load_manifest,
    save_manifest,
)


def write_manifest(tmp_path, data):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class FakeClient:
    """Заглушка WikipediaClient: запоминает вызовы, отдаёт статью с заданной ревизией."""

    def __init__(self, latest_revision: int = 999):
        self.latest_revision = latest_revision
        self.calls = []

    def fetch_article(self, url, revision_id=None):
        self.calls.append((url, revision_id))
        revision = revision_id if revision_id is not None else self.latest_revision
        return RawArticle(
            page_id=1,
            title="Сократ" if "ru." in url else "Python (programming language)",
            language="ru" if "ru." in url else "en",
            url=url,
            html=f'<div class="mw-heading mw-heading2"><h2 id="A">Rev {revision}</h2></div><p>x</p>',
            revision_id=revision,
        )


# --- load_manifest ---------------------------------------------------------


def test_load_manifest_reads_entries_in_order(tmp_path):
    path = write_manifest(tmp_path, {
        "articles": [
            {"url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
             "revision": 123, "file": "python.json"},
            {"url": "https://ru.wikipedia.org/wiki/Сократ",
             "revision": None, "file": "socrates-ru.json"},
        ]
    })

    entries = load_manifest(path)

    assert entries == [
        ManifestEntry(
            url="https://en.wikipedia.org/wiki/Python_(programming_language)",
            revision=123,
            file="python.json",
        ),
        ManifestEntry(
            url="https://ru.wikipedia.org/wiki/Сократ",
            revision=None,
            file="socrates-ru.json",
        ),
    ]


@pytest.mark.parametrize(
    "entry",
    [
        {"revision": 1, "file": "a.json"},  # нет url
        {"url": "https://en.wikipedia.org/wiki/A", "revision": 1},  # нет file
        {"url": "https://example.com/wiki/A", "revision": 1, "file": "a.json"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": 0, "file": "a.json"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": "12", "file": "a.json"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": True, "file": "a.json"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "../a.json"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "a.txt"},
        {"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "manifest.json"},
    ],
)
def test_load_manifest_rejects_invalid_entry(tmp_path, entry):
    path = write_manifest(tmp_path, {"articles": [entry]})

    with pytest.raises(ManifestError):
        load_manifest(path)


def test_load_manifest_rejects_duplicate_file_names(tmp_path):
    path = write_manifest(tmp_path, {
        "articles": [
            {"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "a.json"},
            {"url": "https://en.wikipedia.org/wiki/B", "revision": 2, "file": "a.json"},
        ]
    })

    with pytest.raises(ManifestError):
        load_manifest(path)


def test_load_manifest_rejects_wrong_top_level_shape(tmp_path):
    path = write_manifest(tmp_path, [{"url": "https://en.wikipedia.org/wiki/A"}])

    with pytest.raises(ManifestError):
        load_manifest(path)


# --- save_manifest ---------------------------------------------------------


def test_save_manifest_roundtrip_keeps_cyrillic_readable(tmp_path):
    path = tmp_path / "manifest.json"
    entries = [
        ManifestEntry(url="https://ru.wikipedia.org/wiki/Сократ", revision=5, file="socrates-ru.json"),
    ]

    save_manifest(path, entries)

    text = path.read_text(encoding="utf-8")
    assert "Сократ" in text  # не С...
    assert text.endswith("\n")
    assert load_manifest(path) == entries


def test_kind_is_optional_and_roundtrips(tmp_path):
    # kind - тип статьи (для корпуса проверки устойчивости); у фикстур его нет.
    path = write_manifest(tmp_path, {
        "articles": [
            {"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "a.json", "kind": "person"},
            {"url": "https://en.wikipedia.org/wiki/B", "revision": 2, "file": "b.json"},
        ]
    })

    entries = load_manifest(path)
    assert [e.kind for e in entries] == ["person", None]

    save_manifest(path, entries)
    saved = json.loads(path.read_text(encoding="utf-8"))["articles"]
    assert saved[0]["kind"] == "person"
    assert "kind" not in saved[1]  # манифест без kind пишется как раньше
    assert load_manifest(path) == entries


def test_load_manifest_rejects_non_string_kind(tmp_path):
    path = write_manifest(tmp_path, {
        "articles": [{"url": "https://en.wikipedia.org/wiki/A", "revision": 1, "file": "a.json", "kind": 5}]
    })

    with pytest.raises(ManifestError):
        load_manifest(path)


# --- export_fixtures -------------------------------------------------------


def test_export_uses_pinned_revision_and_does_not_change_manifest(tmp_path):
    entries = [
        ManifestEntry(url="https://en.wikipedia.org/wiki/Python_(programming_language)",
                      revision=123, file="python.json"),
    ]
    client = FakeClient()

    result = export_fixtures(entries, client, tmp_path, update=False)

    assert client.calls == [
        ("https://en.wikipedia.org/wiki/Python_(programming_language)", 123),
    ]
    assert result == entries
    data = json.loads((tmp_path / "python.json").read_text(encoding="utf-8"))
    assert data["sections"][0]["title"] == "Rev 123"


def test_export_twice_gives_identical_files(tmp_path):
    entries = [
        ManifestEntry(url="https://ru.wikipedia.org/wiki/Сократ", revision=7, file="socrates-ru.json"),
    ]

    export_fixtures(entries, FakeClient(), tmp_path, update=False)
    first = (tmp_path / "socrates-ru.json").read_bytes()
    export_fixtures(entries, FakeClient(), tmp_path, update=False)
    second = (tmp_path / "socrates-ru.json").read_bytes()

    assert first == second


def test_export_without_update_refuses_unpinned_entries(tmp_path):
    entries = [
        ManifestEntry(url="https://en.wikipedia.org/wiki/A", revision=1, file="a.json"),
        ManifestEntry(url="https://en.wikipedia.org/wiki/B", revision=None, file="b.json"),
    ]
    client = FakeClient()

    with pytest.raises(ManifestError, match="--update"):
        export_fixtures(entries, client, tmp_path, update=False)

    # Проверка идёт до сети: ничего не скачано и не записано.
    assert client.calls == []
    assert list(tmp_path.iterdir()) == []


def test_export_with_update_fetches_latest_and_pins_its_revision(tmp_path):
    entries = [
        ManifestEntry(url="https://en.wikipedia.org/wiki/Python_(programming_language)",
                      revision=123, file="python.json"),
        ManifestEntry(url="https://ru.wikipedia.org/wiki/Сократ",
                      revision=None, file="socrates-ru.json"),
    ]
    client = FakeClient(latest_revision=999)

    result = export_fixtures(entries, client, tmp_path, update=True)

    assert client.calls == [
        ("https://en.wikipedia.org/wiki/Python_(programming_language)", None),
        ("https://ru.wikipedia.org/wiki/Сократ", None),
    ]
    assert [e.revision for e in result] == [999, 999]
    assert [e.file for e in result] == ["python.json", "socrates-ru.json"]
    # исходный список не изменяется на месте
    assert entries[0].revision == 123
