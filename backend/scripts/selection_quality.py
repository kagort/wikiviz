"""
Качество отбора надёжных данных по разметке владельца (docs/SELECTION_TZ.md, В4-В6).

Читает tests/corpus/review/articles.json (scripts.build_review) и
tests/corpus/review/labels.json (страница /dev/review) и печатает:
  - точность по типам данных: доля показанных значений, размеченных как
    «верно», среди размеченных показанных (цель - не ниже 90%, В4);
  - размеченные «верно», но отброшенные значения (что правила режут зря);
  - «золотые» факты, которые сейчас отброшены (их быть не должно, В5);
  - то же отдельно для контрольной группы (статьи kind="random").

Запуск (из папки backend):
    python -m scripts.selection_quality
"""
import json
from collections import defaultdict
from pathlib import Path

from scripts.build_review import CONTROL_KIND, REVIEW_DIR

TARGET_PRECISION = 0.9
KIND_NAMES = {"event": "даты", "number": "числа", "table": "таблицы", "infobox_field": "инфобокс",
              "image": "изображения", "location": "координаты"}


def load_labels(path: Path) -> dict:
    if not Path(path).exists():
        return {"labels": {}, "golden": []}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"labels": data.get("labels", {}), "golden": data.get("golden", [])}


def quality(articles: list[dict], labels: dict) -> dict:
    """{"main"|"control": {kind: {"ok", "junk", "ok_rejected"}}, "golden_lost": [...] }"""
    marks = labels["labels"]
    golden = set(labels["golden"])
    stats = {"main": defaultdict(lambda: {"ok": 0, "junk": 0, "ok_rejected": 0}),
             "control": defaultdict(lambda: {"ok": 0, "junk": 0, "ok_rejected": 0})}
    golden_lost = []
    for article in articles:
        group = "control" if article["kind"] == CONTROL_KIND else "main"
        for value in article["values"]:
            mark = marks.get(value["key"])
            if value["key"] in golden and not value["selected"]:
                golden_lost.append({**value, "article": article["title"]})
            if mark is None:
                continue
            bucket = stats[group][value["kind"]]
            if value["selected"]:
                bucket["ok" if mark == "ok" else "junk"] += 1
            elif mark == "ok":
                bucket["ok_rejected"] += 1
    return {"main": dict(stats["main"]), "control": dict(stats["control"]), "golden_lost": golden_lost}


def _precision(bucket: dict) -> str:
    total = bucket["ok"] + bucket["junk"]
    return f"{bucket['ok'] / total:.0%}" if total else "—"


def main() -> None:
    articles = json.loads((REVIEW_DIR / "articles.json").read_text(encoding="utf-8"))
    labels = load_labels(REVIEW_DIR / "labels.json")
    result = quality(articles, labels)
    print(f"Размечено значений: {len(labels['labels'])}, золотых фактов: {len(labels['golden'])}\n")
    for group, title in (("main", "Основной корпус"), ("control", "Контрольная группа (случайные статьи)")):
        print(f"## {title}\n")
        print("| Тип | Верно | Мусор | Точность | Верных, но отброшенных |")
        print("|---|---|---|---|---|")
        for kind, name in KIND_NAMES.items():
            bucket = result[group].get(kind)
            if bucket:
                flag = "" if _precision(bucket) == "—" or bucket["ok"] / max(1, bucket["ok"] + bucket["junk"]) >= TARGET_PRECISION else " ⚠"
                print(f"| {name} | {bucket['ok']} | {bucket['junk']} | {_precision(bucket)}{flag} | {bucket['ok_rejected']} |")
        print()
    print(f"## Золотые факты, которые сейчас отброшены: {len(result['golden_lost'])}\n")
    for value in result["golden_lost"]:
        print(f"- {value['article']}: {value['preview'][:80]} — {value['rule']} ({value['reason']})")


if __name__ == "__main__":
    main()
