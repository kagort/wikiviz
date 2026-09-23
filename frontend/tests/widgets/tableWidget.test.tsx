import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { tableWidget } from '../../lib/widgets/tableWidget'
import { makeArticle } from '../fixtures/article'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('tableWidget: контракт', () => {
  test('supports возвращает false для статьи без таблиц', () => {
    expect(tableWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает true для статьи с таблицами (Python)', () => {
    const data = loadFixture('python.json')
    expect(tableWidget.supports(data)).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(tableWidget)
    const data = loadFixture('python.json')

    const selected = selectWidgets(data, registry)

    expect(selected.map((w) => w.id)).toEqual(['table-widget'])
  })

  test('не выбирается для статьи без таблиц', () => {
    const registry = new WidgetRegistry()
    registry.register(tableWidget)

    const selected = selectWidgets(makeArticle(), registry)

    expect(selected).toHaveLength(0)
  })

  test('рендерит все таблицы статьи (Токио: климат + население)', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<tableWidget.render data={data} />)

    expect(screen.getByText('Климат Токио')).toBeInTheDocument()
    // Вторая таблица без title, но её содержимое должно быть на странице
    expect(screen.getAllByRole('table')).toHaveLength(2)
  })
})