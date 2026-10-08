"""
Ручной интеграционный скрипт: выгружает реальные статьи Wikipedia
в NormalizedArticleModel и сохраняет как JSON-фикстуры для frontend-тестов.

Список статей и номера их ревизий лежат в манифесте
frontend/tests/fixtures/real/manifest.json. Обычный запуск скачивает
ровно зафиксированные ревизии, поэтому повторный запуск не меняет фикстуры
(если не менялся код extractor'ов).

Запуск (из папки backend):
    python -m scripts.export_fixtures            # по зафиксированным ревизиям
    python -m scripts.export_fixtures --update   # взять текущие версии статей
                                                 # и записать их ревизии в манифест
"""
import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from app.extractors.article_normalizer import normalize_article
from app.wikipedia.client import WikipediaClient, parse_wikipedia_url
from app.wikipedia.errors import WikipediaError

OUTPUT_DIR = Path(__file__).parent.parent.parent / "frontend" / "tests" / "fixtures" / "real"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


class ManifestError(Exception):
    """Манифест фикстур некорректен или не подходит для выбранного режима."""


@dataclass(frozen=True)
class ManifestEntry:
    url: str
    revision: Optional[int]
    file: str
    # Тип статьи ("person", "city", ...) - используется корпусом проверки
    # устойчивости (scripts.export_corpus); у фикстур его нет.
    kind: Optional[str] = None


def _parse_entry(raw: object, index: int) -> ManifestEntry:
    where = f"manifest entry #{index + 1}"

    if not isinstance(raw, dict):
        raise ManifestError(f"{where}: expected an object")

    url = raw.get("url")
    file = raw.get("file")
    revision = raw.get("revision")
    kind = raw.get("kind")

    if not isinstance(url, str):
        raise ManifestError(f"{where}: 'url' must be a string")
    try:
        parse_wikipedia_url(url)
    except WikipediaError as exc:
        raise ManifestError(f"{where}: bad url: {exc}") from exc

    if (
        not isinstance(file, str)
        or not file.endswith(".json")
        or file == MANIFEST_PATH.name
        or "/" in file
        or "\\" in file
        or file.startswith(".")
    ):
        raise ManifestError(
            f"{where}: 'file' must be a plain *.json file name, got {file!r}"
        )

    # bool - подкласс int в Python, его отсекаем явно.
    if revision is not None and (
        isinstance(revision, bool) or not isinstance(revision, int) or revision <= 0
    ):
        raise ManifestError(
            f"{where}: 'revision' must be a positive integer or null, got {revision!r}"
        )

    if kind is not None and not isinstance(kind, str):
        raise ManifestError(f"{where}: 'kind' must be a string or absent, got {kind!r}")

    return ManifestEntry(url=url, revision=revision, file=file, kind=kind)


def load_manifest(path: Path) -> list[ManifestEntry]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict) or not isinstance(data.get("articles"), list):
        raise ManifestError("manifest must be an object with an 'articles' list")

    entries = [_parse_entry(raw, i) for i, raw in enumerate(data["articles"])]

    files = [entry.file for entry in entries]
    duplicates = sorted({name for name in files if files.count(name) > 1})
    if duplicates:
        raise ManifestError(f"duplicate file names in manifest: {duplicates}")

    return entries


def save_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    articles = []
    for entry in entries:
        item = {"url": entry.url, "revision": entry.revision, "file": entry.file}
        if entry.kind is not None:
            item["kind"] = entry.kind
        articles.append(item)
    data = {"articles": articles}
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def export_fixtures(
    entries: list[ManifestEntry],
    client: WikipediaClient,
    output_dir: Path,
    update: bool = False,
) -> list[ManifestEntry]:
    """
    Скачивает статьи, нормализует и сохраняет фикстуры.

    Без update: берёт только зафиксированные ревизии; если у какой-то
    статьи ревизии нет, ничего не скачивает и сообщает об ошибке.
    С update: берёт текущие версии статей и возвращает манифест
    с их новыми ревизиями (сохранять его - дело вызывающего кода).
    """
    if not update:
        unpinned = [entry.file for entry in entries if entry.revision is None]
        if unpinned:
            raise ManifestError(
                f"no pinned revision for {unpinned}; "
                "run with --update to pin current revisions"
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = []

    for entry in entries:
        revision = None if update else entry.revision
        print(f"Fetching {entry.url} (revision: {revision or 'latest'}) ...")
        raw = client.fetch_article(entry.url, revision_id=revision)
        normalized = normalize_article(raw)

        output_path = output_dir / entry.file
        output_path.write_text(
            normalized.model_dump_json(indent=2),
            encoding="utf-8",
        )
        print(f"  -> saved to {output_path} "
              f"(revision={raw.revision_id}, "
              f"sections={len(normalized.sections)}, "
              f"tables={len(normalized.tables)}, "
              f"locations={len(normalized.locations)}, "
              f"images={len(normalized.images)}, "
              f"events={len(normalized.events)}, "
              f"numbers={len(normalized.numbers)})")

        result.append(replace(entry, revision=raw.revision_id) if update else entry)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--update",
        action="store_true",
        help="fetch current revisions and write them to the manifest",
    )
    args = parser.parse_args()

    entries = load_manifest(MANIFEST_PATH)
    result = export_fixtures(entries, WikipediaClient(), OUTPUT_DIR, update=args.update)

    if args.update:
        save_manifest(MANIFEST_PATH, result)
        print(f"\nManifest updated: {MANIFEST_PATH}")

    print("\nDone.")


if __name__ == "__main__":
    main()
