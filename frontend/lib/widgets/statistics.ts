import type { NumericValue } from '../../types'

/**
 * Чистая логика StatisticsChart (Phase 6): какие группы чисел годятся
 * для столбчатой диаграммы и какой длины столбики.
 *
 * Группа - числа с общим началом подписи до " — " (NumberExtractor
 * пишет так подзаголовок инфобокса: "Religion (2025) — Islam").
 * Пригодна группа из MIN_GROUP_SIZE значений и больше, все в "%".
 * Остальное (годы с единицами "BC"/"до", разнородные единицы Токио,
 * шум вроде "GDP (nominal) — Calling code") в диаграмму не попадает:
 * фильтр осторожный, extractor не чистим (ТЗ, этап 6).
 *
 * Только столбики, не круговая диаграмма: проценты бывают вложенными
 * (France: Christianity 48% включает Catholicism 43%), сумма > 100%.
 */

export const MIN_GROUP_SIZE = 3
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
  const groups = new Map<string, NumericValue[]>()
  for (const number of numbers) {
    const separator = number.label.indexOf(GROUP_SEPARATOR)
    if (separator <= 0) continue
    const title = number.label.slice(0, separator)
    const members = groups.get(title) ?? []
    members.push(number)
    groups.set(title, members)
  }

  const result: ChartGroup[] = []
  for (const [title, members] of groups) {
    if (members.length < MIN_GROUP_SIZE) continue
    if (!members.every((n) => n.unit === PERCENT && Number.isFinite(n.value))) continue
    result.push({
      title,
      unit: PERCENT,
      items: members.map((n) => ({
        label: n.label.slice(title.length + GROUP_SEPARATOR.length),
        value: n.value,
      })),
    })
  }
  return result
}

/**
 * Длина столбика в процентах ширины. Шкала для "%" - от 0 до 100,
 * чтобы 48% выглядело как половина; если значение больше 100,
 * шкала растягивается до наибольшего значения группы.
 */
export function barWidths(items: ChartItem[]): number[] {
  const max = Math.max(100, ...items.map((item) => item.value))
  return items.map((item) => Math.max(0, (item.value / max) * 100))
}

/** Подпись значения: "48%", "37.5%". */
export function formatValue(value: number, unit: string): string {
  return `${Number(value.toFixed(2))}${unit}`
}
