"""
Прогоняет отбор надёжных данных (app/transformers/selection.py) по
сохранённым статьям и записывает результат рядом с ними. Сеть не нужна:
после изменения правил достаточно перезапустить этот скрипт.

    frontend/tests/fixtures/real/*.json  ->  frontend/tests/fixtures/real/selection/*.json
    backend/tests/corpus/articles/*.json ->  backend/tests/corpus/selection/*.json

Заодно пересобирает данные страницы разметки /dev/review
(scripts.build_review).

Запуск (из папки backend):
    python -m scripts.apply_selection
"""
from pathlib import Path

from app.models import NormalizedArticleModel
from app.transformers.selection import select_reliable
from scripts.export_corpus import ARTICLES_DIR, CORPUS_DIR
from scripts.export_fixtures import MANIFEST_PATH as FIXTURES_MANIFEST, OUTPUT_DIR as FIXTURES_DIR

PAIRS = [
    (FIXTURES_DIR, FIXTURES_DIR / "selection"),
    (ARTICLES_DIR, CORPUS_DIR / "selection"),
]


def apply_selection(source_dir: Path, target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(Path(source_dir).glob("*.json")):
        if path.name == FIXTURES_MANIFEST.name:
            continue
        model = NormalizedArticleModel.model_validate_json(path.read_text(encoding="utf-8"))
        result = select_reliable(model)
        (target_dir / path.name).write_text(result.model_dump_json(indent=2), encoding="utf-8")
        count += 1
    return count


def main() -> None:
    for source, target in PAIRS:
        print(f"{source} -> {target}: {apply_selection(source, target)} articles")
    # Данные страницы разметки /dev/review зависят от результатов отбора.
    from scripts.build_review import main as build_review_main
    build_review_main()


if __name__ == "__main__":
    main()
