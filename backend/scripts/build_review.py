"""
Данные для страницы разметки /dev/review (docs/SELECTION_TZ.md, В5-В6).

Без сети, по сохранённому корпусу и результатам отбора:
    tests/corpus/review/articles.json - по каждой статье все значения:
        показано ли, а если отброшено - правило и причина;
    tests/corpus/review/sample.json  - случайная выборка ~100 показанных
        значений по типам для оценки точности (без контрольной группы -
        статей kind="random").

Ключ значения строится по содержанию (а не по номеру в списке), чтобы
разметка владельца (review/labels.json) переживала перевыгрузку корпуса.

Запуск (из папки backend), после изменения правил отбора:
    python -m scripts.build_review
"""
import json
import random
from collections import Counter
from pathlib import Path

from app.models import NormalizedArticleModel, SelectionResult
from scripts.export_corpus import ARTICLES_DIR, CORPUS_DIR, MANIFEST_PATH
from scripts.export_fixtures import load_manifest

REVIEW_DIR = CORPUS_DIR / "review"
SELECTION_DIR = CORPUS_DIR / "selection"
CONTROL_KIND = "random"
SAMPLE_SEED = 2026
SAMPLE_QUOTAS = {"event": 25, "infobox_field": 20, "image": 20, "table": 15, "number": 15, "location": 5}

_BLOCK_NAMES = {
    "infobox": "инфобокс", "paragraph": "абзац", "list_item": "пункт списка", "table": "таблица",
    "figure": "иллюстрация", "gallery": "галерея", "other": "другое",
}


def _where(context) -> str:
    if context is None:
        return ""
    parts = [_BLOCK_NAMES.get(context.block.value, context.block.value)]
    if context.section_path:
        parts.append(" › ".join(context.section_path))
    return ", ".join(parts)


def article_values(file: str, model: NormalizedArticleModel, selection: SelectionResult) -> list[dict]:
    """Все значения статьи в порядке типов: события, числа, таблицы, инфобокс, изображения, координаты."""
    rejected = {(r.kind, r.ref): r for r in selection.rejected}
    values: list[dict] = []
    used: Counter = Counter()

    def add(kind: str, ref: str, identity: str, preview: str, **extra) -> None:
        base = f"{file}|{kind}|{identity}"
        used[base] += 1
        key = base if used[base] == 1 else f"{base}#{used[base]}"
        rejection = rejected.get((kind, ref))
        values.append({
            "key": key, "kind": kind, "preview": preview,
            "selected": rejection is None,
            "rule": rejection.rule if rejection else None,
            "reason": rejection.reason if rejection else None,
            **extra,
        })

    for event in model.events:
        add("event", event.id, f"{event.date}|{event.title}|{event.source.value}",
            f"{event.date} — {event.title}", where=_where(event.context))
    for index, number in enumerate(model.numbers):
        add("number", str(index), f"{number.label}|{number.value:g}|{number.unit}",
            f"{number.label} = {number.value:g} {number.unit or ''}".strip())
    for table in model.tables:
        name = table.title or " | ".join(table.columns[:3])
        first_row = " | ".join(table.rows[0][:4]) if table.rows else ""
        add("table", table.id, name,
            f"{name} ({len(table.rows)} строк × {len(table.columns)} колонок)", detail=first_row)
    for key, field in model.infobox.items():
        label = f"{field.group} › {field.label}" if field.group else field.label
        add("infobox_field", key, key, f"{label}: {field.value}")
    for index, image in enumerate(model.images):
        file_name = image.url.rsplit("/", 1)[-1].split("?")[0]
        add("image", str(index), file_name, image.caption or "(без подписи)",
            thumbnail=image.thumbnail_url or image.url, where=_where(image.context))
    for index, location in enumerate(model.locations):
        add("location", str(index), f"{location.latitude:.4f},{location.longitude:.4f}",
            f"{location.name}: {location.latitude:.4f}, {location.longitude:.4f}")
    return values


def build_review(corpus_dir: Path = CORPUS_DIR) -> tuple[list[dict], list[dict]]:
    articles = []
    for entry in load_manifest(Path(corpus_dir) / MANIFEST_PATH.name):
        model_path = Path(corpus_dir) / ARTICLES_DIR.name / entry.file
        selection_path = Path(corpus_dir) / SELECTION_DIR.name / entry.file
        if not model_path.exists() or not selection_path.exists():
            continue
        model = NormalizedArticleModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        selection = SelectionResult.model_validate_json(selection_path.read_text(encoding="utf-8"))
        articles.append({
            "file": entry.file, "kind": entry.kind, "title": model.article.title,
            "url": model.article.url, "values": article_values(entry.file, model, selection),
        })

    rng = random.Random(SAMPLE_SEED)
    sample = []
    for kind, quota in SAMPLE_QUOTAS.items():
        pool = [
            {**value, "article": article["title"], "file": article["file"]}
            for article in articles if article["kind"] != CONTROL_KIND
            for value in article["values"] if value["kind"] == kind and value["selected"]
        ]
        sample.extend(rng.sample(pool, min(quota, len(pool))))
    return articles, sample


def main() -> None:
    articles, sample = build_review()
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in (("articles.json", articles), ("sample.json", sample)):
        (REVIEW_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"articles: {len(articles)}, values: {sum(len(a['values']) for a in articles)}, sample: {len(sample)}")
    print("sample by kind:", dict(Counter(v["kind"] for v in sample)))


if __name__ == "__main__":
    main()
