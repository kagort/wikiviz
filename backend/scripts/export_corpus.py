"""
Корпус проверки устойчивости (план, сессия 2): выгружает статьи разных
типов через нормализатор и сохраняет результат для офлайн-анализа
(scripts.corpus_report) и будущих тестов правил отбора.

В отличие от export_fixtures, падение на одной статье не останавливает
прогон: ошибка записывается в errors.json - найти такие падения и есть
цель проверки.

Файлы (папка backend/tests/corpus):
    manifest.json   - статьи, ревизии, тип статьи (kind)
    articles/*.json - NormalizedArticleModel по каждой статье
    errors.json     - статьи, на которых упала загрузка или нормализация

Запуск (из папки backend, нужна сеть):
    python -m scripts.export_corpus                        # по закреплённым ревизиям
    python -m scripts.export_corpus --pin-missing          # закрепить ревизии новых статей и выгрузить
    python -m scripts.export_corpus --add-random 3 --lang en   # добавить в манифест 3 случайные статьи
    python -m scripts.export_corpus --add-stub --lang ru       # добавить короткую статью-заготовку
После --add-* нужен запуск с --pin-missing.
"""
import argparse
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx

from app.extractors.article_normalizer import normalize_article
from app.wikipedia.client import WikipediaClient
from scripts.export_fixtures import ManifestEntry, load_manifest, save_manifest

CORPUS_DIR = Path(__file__).parent.parent / "tests" / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"
ARTICLES_DIR = CORPUS_DIR / "articles"
ERRORS_PATH = CORPUS_DIR / "errors.json"

# Статья-заготовка: вики-текст короче этого числа байт.
STUB_MAX_LENGTH = 3000
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _error_text(exc: BaseException) -> str:
    # Только тип и сообщение: без трассировки, чтобы errors.json не менялся
    # от правок кода, не связанных с ошибкой.
    return f"{type(exc).__name__}: {exc}"


def export_corpus(
    entries: list[ManifestEntry],
    client,
    articles_dir: Path,
    pin_missing: bool = False,
) -> tuple[list[ManifestEntry], list[dict]]:
    """
    Выгружает статьи корпуса. Возвращает манифест (с новыми ревизиями,
    если pin_missing) и список ошибок вида
    {"file", "url", "stage": "unpinned"|"fetch"|"normalize", "error"}.
    """
    articles_dir = Path(articles_dir)
    articles_dir.mkdir(parents=True, exist_ok=True)
    result: list[ManifestEntry] = []
    errors: list[dict] = []

    for entry in entries:
        if entry.revision is None and not pin_missing:
            errors.append({"file": entry.file, "url": entry.url, "stage": "unpinned",
                           "error": "no pinned revision; run with --pin-missing"})
            result.append(entry)
            continue

        print(f"Fetching {entry.url} (revision: {entry.revision or 'latest'}) ...")
        try:
            raw = client.fetch_article(entry.url, revision_id=entry.revision)
        except Exception as exc:  # noqa: BLE001 - фиксируем любую ошибку загрузки
            errors.append({"file": entry.file, "url": entry.url, "stage": "fetch",
                           "error": _error_text(exc)})
            result.append(entry)
            continue

        pinned = entry if entry.revision is not None else replace(entry, revision=raw.revision_id)
        result.append(pinned)

        try:
            normalized = normalize_article(raw)
        except Exception as exc:  # noqa: BLE001 - падение нормализатора и ищем
            errors.append({"file": entry.file, "url": entry.url, "stage": "normalize",
                           "error": _error_text(exc)})
            continue

        (articles_dir / entry.file).write_text(
            normalized.model_dump_json(indent=2), encoding="utf-8"
        )

    return result, errors


def _api_get(client: WikipediaClient, lang: str, params: dict) -> dict:
    response = httpx.get(
        f"https://{lang}.wikipedia.org/w/api.php",
        params={**params, "format": "json", "formatversion": "2"},
        headers={"User-Agent": client.user_agent},
        timeout=client.timeout,
        trust_env=False,
    )
    response.raise_for_status()
    return response.json()


def _file_name(prefix: str, lang: str, title: str, page_id: int) -> str:
    slug = _SLUG_RE.sub("-", title.lower()).strip("-")
    if not slug or slug != slug.encode("ascii", "ignore").decode():
        slug = str(page_id)
    return f"{prefix}-{lang}-{slug[:60]}.json"


def pick_random(
    client: WikipediaClient, lang: str, count: int, kind: str,
    max_length: Optional[int] = None, attempts: int = 200,
) -> list[ManifestEntry]:
    """Случайные статьи основного пространства (Special:Random); для заготовок - с ограничением длины."""
    picked: list[ManifestEntry] = []
    for _ in range(attempts):
        if len(picked) >= count:
            break
        data = _api_get(client, lang, {
            "action": "query", "generator": "random", "grnnamespace": "0",
            "grnlimit": "10", "prop": "info|pageprops",
        })
        for page in data["query"]["pages"]:
            if len(picked) >= count:
                break
            if max_length is not None and page.get("length", 0) > max_length:
                continue
            title = page["title"]
            # Читаемый адрес, как в манифесте фикстур: кодируются только
            # символы, ломающие URL.
            path = "".join(
                quote(c) if c in "?#%&+" else c for c in title.replace(" ", "_")
            )
            url = f"https://{lang}.wikipedia.org/wiki/{path}"
            picked.append(ManifestEntry(
                url=url, revision=None,
                file=_file_name(kind, lang, title, page["pageid"]), kind=kind,
            ))
    if len(picked) < count:
        raise RuntimeError(f"picked only {len(picked)} of {count} {kind} articles in {lang}")
    return picked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--pin-missing", action="store_true",
                        help="pin revisions of entries without one, then export")
    parser.add_argument("--add-random", type=int, metavar="N",
                        help="append N random articles to the manifest")
    parser.add_argument("--add-stub", action="store_true",
                        help=f"append one short article (< {STUB_MAX_LENGTH} bytes)")
    parser.add_argument("--lang", choices=["en", "ru"], help="language for --add-*")
    args = parser.parse_args()

    client = WikipediaClient()
    entries = load_manifest(MANIFEST_PATH)

    if args.add_random or args.add_stub:
        if not args.lang:
            parser.error("--add-random/--add-stub need --lang")
        new = (pick_random(client, args.lang, args.add_random, "random") if args.add_random
               else pick_random(client, args.lang, 1, "stub", max_length=STUB_MAX_LENGTH))
        existing = {e.file for e in entries}
        new = [e for e in new if e.file not in existing]
        save_manifest(MANIFEST_PATH, entries + new)
        for entry in new:
            print(f"added {entry.kind}: {entry.url} -> {entry.file}")
        print("\nNow run with --pin-missing.")
        return

    result, errors = export_corpus(entries, client, ARTICLES_DIR, pin_missing=args.pin_missing)
    if args.pin_missing:
        save_manifest(MANIFEST_PATH, result)
    ERRORS_PATH.write_text(json.dumps(errors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nArticles: {len(entries)}, exported: {len(entries) - len(errors)}, errors: {len(errors)}")
    for error in errors:
        print(f"  {error['stage']:9} {error['file']}: {error['error']}")


if __name__ == "__main__":
    main()
