/**
 * Разметка владельца для оценки отбора надёжных данных
 * (docs/SELECTION_TZ.md, В5-В6). Хранится в
 * backend/tests/corpus/review/labels.json; считает её
 * python -m scripts.selection_quality.
 */

export type Mark = 'ok' | 'junk'

export interface ReviewLabels {
  /** Ключ значения -> «верно» или «мусор» (выборка для точности, В6). */
  labels: Record<string, Mark>
  /** Ключи «золотых» фактов: обязаны остаться после отбора (В5). */
  golden: string[]
}

/** Значение статьи корпуса (scripts.build_review). */
export interface ReviewValue {
  key: string
  kind: string
  preview: string
  selected: boolean
  rule: string | null
  reason: string | null
  where?: string
  detail?: string
  thumbnail?: string
}

export interface ReviewArticle {
  file: string
  kind: string
  title: string
  url: string
  values: ReviewValue[]
}

/** Элемент выборки для точности: значение + статья. */
export interface SampleValue extends ReviewValue {
  article: string
  file: string
}

export const EMPTY_LABELS: ReviewLabels = { labels: {}, golden: [] }

/** Ставит или снимает (mark = null) отметку; исходный объект не меняется. */
export function setMark(current: ReviewLabels, key: string, mark: Mark | null): ReviewLabels {
  const labels = { ...current.labels }
  if (mark === null) delete labels[key]
  else labels[key] = mark
  return { ...current, labels }
}

export function toggleGolden(current: ReviewLabels, key: string): ReviewLabels {
  const golden = current.golden.includes(key)
    ? current.golden.filter((k) => k !== key)
    : [...current.golden, key]
  return { ...current, golden }
}

/**
 * Проверяет присланную разметку и приводит её к стабильному виду
 * (ключи по алфавиту, без повторов) - чтобы файл в git менялся только
 * по существу. Бросает Error на неверной форме.
 */
export function parseLabels(data: unknown): ReviewLabels {
  if (typeof data !== 'object' || data === null) throw new Error('labels: ожидается объект')
  const { labels, golden } = data as { labels?: unknown; golden?: unknown }
  if (typeof labels !== 'object' || labels === null || Array.isArray(labels)) {
    throw new Error('labels.labels: ожидается объект')
  }
  if (!Array.isArray(golden) || !golden.every((k) => typeof k === 'string')) {
    throw new Error('labels.golden: ожидается список строк')
  }
  const sorted: Record<string, Mark> = {}
  for (const key of Object.keys(labels).sort()) {
    const mark = (labels as Record<string, unknown>)[key]
    if (mark !== 'ok' && mark !== 'junk') throw new Error(`labels.labels[${key}]: ожидается "ok" или "junk"`)
    sorted[key] = mark
  }
  return { labels: sorted, golden: [...new Set(golden as string[])].sort() }
}

/** Сколько значений из списка уже размечено. */
export function countMarked(keys: string[], current: ReviewLabels): number {
  return keys.filter((key) => key in current.labels).length
}
