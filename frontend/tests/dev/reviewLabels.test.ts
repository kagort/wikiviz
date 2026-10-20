import {
  EMPTY_LABELS,
  countMarked,
  parseLabels,
  setMark,
  toggleGolden,
} from '../../lib/dev/reviewLabels'

describe('reviewLabels', () => {
  test('setMark ставит, меняет и снимает отметку, не меняя исходный объект', () => {
    const marked = setMark(EMPTY_LABELS, 'k1', 'ok')
    expect(marked.labels).toEqual({ k1: 'ok' })
    expect(EMPTY_LABELS.labels).toEqual({})
    expect(setMark(marked, 'k1', 'junk').labels).toEqual({ k1: 'junk' })
    expect(setMark(marked, 'k1', null).labels).toEqual({})
  })

  test('toggleGolden добавляет и убирает золотой факт', () => {
    const once = toggleGolden(EMPTY_LABELS, 'k1')
    expect(once.golden).toEqual(['k1'])
    expect(toggleGolden(once, 'k1').golden).toEqual([])
  })

  test('parseLabels сортирует ключи и убирает повторы золотых фактов', () => {
    const parsed = parseLabels({ labels: { b: 'junk', a: 'ok' }, golden: ['z', 'y', 'z'] })
    expect(Object.keys(parsed.labels)).toEqual(['a', 'b'])
    expect(parsed.golden).toEqual(['y', 'z'])
  })

  test.each([
    null,
    [],
    { labels: [], golden: [] },
    { labels: { a: 'maybe' }, golden: [] },
    { labels: {}, golden: [1] },
    { labels: {} },
  ])('parseLabels отклоняет неверную форму: %p', (data) => {
    expect(() => parseLabels(data)).toThrow()
  })

  test('countMarked считает только размеченные ключи из списка', () => {
    const labels = { labels: { a: 'ok' as const, c: 'junk' as const }, golden: [] }
    expect(countMarked(['a', 'b', 'c'], labels)).toBe(2)
  })
})
