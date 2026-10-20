import type { NumericValue } from '../../types'

/**
 * Чистая логика StatisticsChart: группы чисел для столбчатой диаграммы
 * и длина столбиков.
 *
 * Виджет получает уже отобранные числа (backend, docs/SELECTION_TZ.md):
 * отбор оставляет только числа с распознанной единицей, без кодов и
 * годов, в группах из 3 и больше значений (правила NUM-*). Здесь числа
 * лишь раскладываются по группам: общее начало подписи до " — "
 * (NumberExtractor пишет так подзаголовок инфобокса: "Religion (2025) —
 * Islam") и одна единица измерения.
 *
 * Только столбики, не круговая диаграмма: проценты бывают вложенными
 * (France: Christianity 48% включает Catholicism 43%), сумма > 100%.
 */

const GROUP_SEPARATOR = ' — '
const PERCENT = '%'

export interface ChartItem {
  label: string
  value: number
}

export interface ChartGroup {
  title: string
  unit: string
  items: ChartItem[]
}

export function findChartGroups(numbers: NumericValue[]): ChartGroup[] {
  const groups = new Map<string, ChartGroup>()
  for (const number of numbers) {
    const separator = number.label.indexOf(GROUP_SEPARATOR)
    if (separator <= 0 || number.unit === null || !Number.isFinite(number.value)) continue
    const title = number.label.slice(0, separator)
    const key = `${title}\u0000${number.unit}`
    const group = groups.get(key) ?? { title, unit: number.unit, items: [] }
    group.items.push({
      label: number.label.slice(separator + GROUP_SEPARATOR.length),
      value: number.value,
    })
    groups.set(key, group)
  }
  return [...groups.values()]
}

/**
 * Длина столбика в процентах ширины. Для "%" шкала от 0 до 100, чтобы
 * 48% выглядело как половина (если значение больше 100 - до максимума);
 * для других единиц - от 0 до наибольшего значения группы.
 */
export function barWidths(items: ChartItem[], unit: string = PERCENT): number[] {
  const values = items.map((item) => item.value)
  const max = unit === PERCENT ? Math.max(100, ...values) : Math.max(...values)
  if (!(max > 0)) return items.map(() => 0)
  return items.map((item) => Math.max(0, (item.value / max) * 100))
}

/** Подпись значения: "48%", "37.5%", "2193.96 км²". */
export function formatValue(value: number, unit: string): string {
  const number = Number(value.toFixed(2))
  return unit === PERCENT ? `${number}${unit}` : `${number} ${unit}`
}
