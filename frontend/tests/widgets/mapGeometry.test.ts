import fs from 'node:fs'
import path from 'node:path'
import { computeMapView, formatPopupText } from '../../lib/widgets/mapGeometry'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('computeMapView', () => {
  test('пустой список даёт null', () => {
    expect(computeMapView([])).toBeNull()
  })

  test('одна точка (Токио) даёт фиксированный центр и zoom', () => {
    const data = loadFixture('tokyo-ru.json')
    const view = computeMapView(data.locations)
    expect(view).toEqual({
      kind: 'single',
      center: [35.7, 139.6],
      zoom: 10,
    })
  })

  test('несколько точек (France) дают bounding box', () => {
    const data = loadFixture('france.json')
    const view = computeMapView(data.locations)
    expect(view).toEqual({
      kind: 'bounds',
      bounds: [
        [47.0, 2.0],
        [48.85, 2.35],
      ],
    })
  })
})

describe('formatPopupText', () => {
  test('включает координаты даже без description (Токио)', () => {
    const data = loadFixture('tokyo-ru.json')
    const text = formatPopupText(data.locations[0])
    expect(text).toBe('Токио - 35.7000, 139.6000')
  })

  test('две точки France с одинаковым name дают разный текст попапа', () => {
    const data = loadFixture('france.json')
    const [first, second] = data.locations
    expect(first.name).toBe(second.name) // подтверждаем находку разведки
    expect(formatPopupText(first)).not.toBe(formatPopupText(second))
  })

  test('description добавляется в текст, если он есть', () => {
    const text = formatPopupText({
      id: 'x',
      name: 'Test',
      latitude: 1,
      longitude: 2,
      description: 'Столица',
      source: 'coordinate' as never,
      confidence: 1,
    })
    expect(text).toBe('Test - Столица - 1.0000, 2.0000')
  })
})