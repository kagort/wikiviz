import { DatePrecision, SourceType } from '../../types'
import type { Event } from '../../types'

/**
 * Чистая логика TimelineWidget (Phase 6): разбор, сортировка и подпись дат.
 *
 * Формат date от backend (ТЗ §16.2):
 *   "YYYY-MM-DD" - день; "-YYYY" - год до н. э. (упрощённая нумерация,
 *   без смещения на единицу: "-0044" = 44 до н. э.).
 * Некорректные строки не роняют виджет: такие события идут в конец
 * списка и показываются как есть.
 */

export interface ParsedDate {
  year: number
  month: number | null
  day: number | null
}

const DATE_RE = /^(-?)(\d{1,4})(?:-(\d{2})(?:-(\d{2}))?)?$/

export function parseEventDate(date: string): ParsedDate | null {
  const match = DATE_RE.exec(date.trim())
  if (!match) return null

  const [, sign, yearText, monthText, dayText] = match
  const year = Number(yearText) * (sign === '-' ? -1 : 1)
  const month = monthText ? Number(monthText) : null
  const day = dayText ? Number(dayText) : null

  if (month !== null && (month < 1 || month > 12)) return null
  if (day !== null && (day < 1 || day > 31)) return null

  return { year, month, day }
}

/**
 * Сортировка по возрастанию даты. Год без дня и месяца стоит перед
 * конкретными днями того же года. Одинаковые даты и некорректные строки
 * сохраняют исходный порядок; некорректные - в конце.
 */
export function sortEvents(events: Event[]): Event[] {
  const keyed = events.map((event, index) => ({
    event,
    index,
    parsed: parseEventDate(event.date),
  }))

  keyed.sort((a, b) => {
    if (a.parsed === null || b.parsed === null) {
      if (a.parsed === null && b.parsed === null) return a.index - b.index
      return a.parsed === null ? 1 : -1
    }
    return (
      a.parsed.year - b.parsed.year ||
      (a.parsed.month ?? 0) - (b.parsed.month ?? 0) ||
      (a.parsed.day ?? 0) - (b.parsed.day ?? 0) ||
      a.index - b.index
    )
  })

  return keyed.map(({ event }) => event)
}

const EN_MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

// Родительный падеж для дня ("14 марта"), именительный для месяца ("март 1879").
const RU_MONTHS_GENITIVE = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]
const RU_MONTHS_NOMINATIVE = [
  'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
  'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
]

function formatYear(year: number, language: string): string {
  if (year >= 0) return String(year)
  return language === 'ru' ? `${-year} до н. э.` : `${-year} BC`
}

/**
 * Подпись даты по-человечески с учётом точности и языка статьи:
 * "14 March 1879", "14 марта 1879", "44 BC", "44 до н. э.".
 * Языки, кроме ru, подписываются по-английски. Точности decade,
 * century, unknown и некорректные строки показываются как есть.
 */
export function formatEventDate(event: Event, language: string): string {
  const parsed = parseEventDate(event.date)
  if (parsed === null) return event.date

  const ru = language === 'ru'
  const year = formatYear(parsed.year, language)

  switch (event.date_precision) {
    case DatePrecision.Day:
      if (parsed.month === null || parsed.day === null) return year
      return ru
        ? `${parsed.day} ${RU_MONTHS_GENITIVE[parsed.month - 1]} ${year}`
        : `${parsed.day} ${EN_MONTHS[parsed.month - 1]} ${year}`
    case DatePrecision.Month:
      if (parsed.month === null) return year
      return ru
        ? `${RU_MONTHS_NOMINATIVE[parsed.month - 1]} ${year}`
        : `${EN_MONTHS[parsed.month - 1]} ${year}`
    case DatePrecision.Year:
      return year
    default:
      return event.date
  }
}

const SOURCE_LABELS: Partial<Record<SourceType, string>> = {
  [SourceType.Infobox]: 'инфобокс',
  [SourceType.ArticleText]: 'текст статьи',
}

/** Пометка источника и уверенности: "инфобокс, 100%", "текст статьи, 60%". */
export function formatEventSource(event: Event): string {
  const source = SOURCE_LABELS[event.source] ?? event.source
  return `${source}, ${Math.round(event.confidence * 100)}%`
}
