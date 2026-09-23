import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { galleryWidget } from '../../lib/widgets/galleryWidget'
import { makeArticle } from '../fixtures/article'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('galleryWidget: контракт', () => {
  test('supports возвращает false для статьи без изображений', () => {
    expect(galleryWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает true для статьи с изображениями (Python)', () => {
    const data = loadFixture('python.json')
    expect(galleryWidget.supports(data)).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(galleryWidget)
    const data = loadFixture('python.json')

    const selected = selectWidgets(data, registry)

    expect(selected.map((w) => w.id)).toEqual(['gallery-widget'])
  })

  test('не выбирается для статьи без изображений', () => {
    const registry = new WidgetRegistry()
    registry.register(galleryWidget)

    const selected = selectWidgets(makeArticle(), registry)

    expect(selected).toHaveLength(0)
  })

  test('рендерит все изображения статьи (Токио: 3 превью)', () => {
    const data = loadFixture('tokyo-ru.json')
    const { container } = render(<galleryWidget.render data={data} />)

    expect(container.querySelectorAll('img')).toHaveLength(3)
  })
})