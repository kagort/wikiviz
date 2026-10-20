import type { NormalizedArticleModel } from "./articleModel";

/** Значение, не прошедшее отбор надёжных данных (docs/SELECTION_TZ.md, В3). */
export interface RejectedValue {
  /** event, number, image, table, infobox_field, location */
  kind: string;
  ref: string;
  preview: string;
  /** Код правила: EV-LIST, NUM-UNIT, ... */
  rule: string;
  reason: string;
}

/** Результат отбора: отобранная модель для виджетов и отброшенное с причинами. Синхронно с backend/app/models/selection.py. */
export interface SelectionResult {
  selected: NormalizedArticleModel;
  rejected: RejectedValue[];
}
