from typing import List

from pydantic import BaseModel

from app.models.article_model import NormalizedArticleModel


class RejectedValue(BaseModel):
    """
    Значение, не прошедшее отбор надёжных данных (docs/SELECTION_TZ.md, В3).

    kind - тип значения: event, number, image, table, infobox_field, location;
    ref - ссылка на значение (id события, ключ поля инфобокса, id таблицы,
    номер в списке); preview - короткий человекочитаемый вид;
    rule - код правила (EV-LIST, NUM-UNIT ...); reason - причина по-русски.
    """

    kind: str
    ref: str
    preview: str
    rule: str
    reason: str


class SelectionResult(BaseModel):
    """Результат отбора: отобранная модель (для виджетов) и отброшенное с причинами."""

    selected: NormalizedArticleModel
    rejected: List[RejectedValue] = []
