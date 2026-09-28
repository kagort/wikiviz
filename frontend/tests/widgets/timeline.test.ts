import {
  parseEventDate,
  sortEvents,
  formatEventDate,
  formatEventSource,
} from '../../lib/widgets/timeline'
import { DatePrecision, SourceType } from '../../types'
import type { Event } from '../../types'

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: 'e',
    date: '1879-03-14',
    date_precision: DatePrecision.Day,
    title: 'Born',
    description: null,
    source: SourceType.Infobox,
    confidence: 1.0,
    ...overrides,
  }
}

describe('parseEventDate', () => {
  test('полная дата', () => {
    expect(parseEventDate('1879-03-14')).toEqual({ year: 1879, month: 3, day: 14 })
  })

  test('год до н. э. в формате -000N', () => {
    expect(parseEventDate('-0044')).toEqual({ year: -44, month: null, day: null })
  })

  test('некорректные строки дают null, а не исключение', () => {
    for (const bad of ['', 'abc', '1879-13-01', '1879-03-32', '12345', '1879/03/14']) {
      expect(parseEventDate(bad)).toBeNull()
    }
  })
})

describe('sortEvents', () => {
  test('годы до н. э. идут раньше и в правильном порядке (-100 раньше -44)', () => {
    const events = [
      makeEvent({ id: 'a', date: '1945-06-26' }),
      makeEvent({ id: 'b', date: '-0044', date_precision: DatePrecision.Year }),
      makeEvent({ id: 'c', date: '-0100', date_precision: DatePrecision.Year }),
    ]

    expect(sortEvents(events).map((e) => e.id)).toEqual(['c', 'b', 'a'])
  })

  test('год без дня стоит перед конкретными днями того же года', () => {
    const events = [
      makeEvent({ id: 'day', date: '1945-03-10' }),
      makeEvent({ id: 'year', date: '1945', date_precision: DatePrecision.Year }),
    ]

    expect(sortEvents(events).map((e) => e.id)).toEqual(['year', 'day'])
  })

  test('одинаковые даты сохраняют исходный порядок', () => {
    const events = [
      makeEvent({ id: 'first', date: '-0044', date_precision: DatePrecision.Year }),
      makeEvent({ id: 'second', date: '-0044', date_precision: DatePrecision.Year }),
      makeEvent({ id: 'third', date: '-0044', date_precision: DatePrecision.Year }),
    ]

    expect(sortEvents(events).map((e) => e.id)).toEqual(['first', 'second', 'third'])
  })

  test('некорректные даты уходят в конец, не ломая сортировку остальных', () => {
    const events = [
      makeEvent({ id: 'bad1', date: 'garbage' }),
      makeEvent({ id: 'late', date: '2000-01-01' }),
      makeEvent({ id: 'bad2', date: '' }),
      makeEvent({ id: 'early', date: '1900-01-01' }),
    ]

    expect(sortEvents(events).map((e) => e.id)).toEqual(['early', 'late', 'bad1', 'bad2'])
  })

  test('не меняет исходный массив', () => {
    const events = [makeEvent({ id: 'b', date: '2000-01-01' }), makeEvent({ id: 'a', date: '1900-01-01' })]
    sortEvents(events)
    expect(events.map((e) => e.id)).toEqual(['b', 'a'])
  })
})

describe('formatEventDate', () => {
  test('день по-английски', () => {
    expect(formatEventDate(makeEvent(), 'en')).toBe('14 March 1879')
  })

  test('день по-русски в родительном падеже', () => {
    expect(formatEventDate(makeEvent(), 'ru')).toBe('14 марта 1879')
  })

  test('год до н. э. подписывается по языку статьи', () => {
    const event = makeEvent({ date: '-0044', date_precision: DatePrecision.Year })
    expect(formatEventDate(event, 'en')).toBe('44 BC')
    expect(formatEventDate(event, 'ru')).toBe('44 до н. э.')
  })

  test('обычный год', () => {
    const event = makeEvent({ date: '1945', date_precision: DatePrecision.Year })
    expect(formatEventDate(event, 'ru')).toBe('1945')
  })

  test('месяц: по-русски в именительном падеже', () => {
    const event = makeEvent({ date: '1879-03', date_precision: DatePrecision.Month })
    expect(formatEventDate(event, 'en')).toBe('March 1879')
    expect(formatEventDate(event, 'ru')).toBe('март 1879')
  })

  test('неизвестный язык подписывается по-английски', () => {
    expect(formatEventDate(makeEvent(), 'de')).toBe('14 March 1879')
  })

  test('точность unknown показывается как есть', () => {
    const event = makeEvent({ date: '1879-03-14', date_precision: DatePrecision.Unknown })
    expect(formatEventDate(event, 'en')).toBe('1879-03-14')
  })

  test('некорректная строка показывается как есть и не роняет', () => {
    const event = makeEvent({ date: 'около 1500' })
    expect(formatEventDate(event, 'ru')).toBe('около 1500')
  })

  test('точность day без дня в строке показывает только год', () => {
    const event = makeEvent({ date: '-0044', date_precision: DatePrecision.Day })
    expect(formatEventDate(event, 'en')).toBe('44 BC')
  })
})

describe('formatEventSource', () => {
  test('инфобокс и текст статьи с уверенностью в процентах', () => {
    expect(formatEventSource(makeEvent())).toBe('инфобокс, 100%')
    expect(
      formatEventSource(makeEvent({ source: SourceType.ArticleText, confidence: 0.6 }))
    ).toBe('текст статьи, 60%')
  })
})
