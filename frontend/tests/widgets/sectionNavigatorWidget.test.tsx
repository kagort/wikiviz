import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { sectionNavigatorWidget } from '../../lib/widgets/sectionNavigatorWidget'
import { flattenSections } from '../../lib/widgets/sectionAnchors'
import { makeArticle } from '../fixtures/article'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('sectionNavigatorWidget: контракт', () => {
  test('supports возвращает false для статьи без разделов', () => {
    expect(sectionNavigatorWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает true для статьи с разделами (Python)', () => {
    expect(sectionNavigatorWidget.supports(loadFixture('python.json'))).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(sectionNavigatorWidget)
    const selected = selectWidgets(loadFixture('python.json'), registry)
    expect(selected.map((w) => w.id)).toEqual(['section-navigator-widget'])
  })

  test('не выбирается для статьи без разделов', () => {
    const registry = new WidgetRegistry()
    registry.register(sectionNavigatorWidget)
    expect(selectWidgets(makeArticle(), registry)).toHaveLength(0)
  })

  test('рендерит ссылки на все разделы статьи (Токио)', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<sectionNavigatorWidget.render data={data} />)
    expect(screen.getAllByRole('link')).toHaveLength(flattenSections(data.sections).length)
  })
})