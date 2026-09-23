import fs from 'node:fs'
import path from 'node:path'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { mapWidget } from '../../lib/widgets/mapWidget'
import { makeArticle } from '../fixtures/article'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

// Рендер MapWidgetView (реальный Leaflet) намеренно не тестируется юнит-тестами:
// dynamic(ssr:false) в тестовой среде не рендерит настоящую карту, а сам Leaflet
// ненадёжен в jsdom. Проверено визуально на dev-странице /dev/map -
// см. Phase 6 контекст-документ.
describe('mapWidget: контракт', () => {
  test('supports возвращает false для статьи без локаций (Python)', () => {
    const data = loadFixture('python.json')
    expect(mapWidget.supports(data)).toBe(false)
  })

  test('supports возвращает false для пустой статьи', () => {
    expect(mapWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает true для статьи с локациями (France)', () => {
    const data = loadFixture('france.json')
    expect(mapWidget.supports(data)).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(mapWidget)
    const data = loadFixture('france.json')

    const selected = selectWidgets(data, registry)

    expect(selected.map((w) => w.id)).toEqual(['map-widget'])
  })

  test('не выбирается для статьи без локаций', () => {
    const registry = new WidgetRegistry()
    registry.register(mapWidget)

    const selected = selectWidgets(loadFixture('python.json'), registry)

    expect(selected).toHaveLength(0)
  })
})