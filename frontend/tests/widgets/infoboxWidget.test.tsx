import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { infoboxWidget } from '../../lib/widgets/infoboxWidget'
import { groupInfoboxFields } from '../../lib/widgets/infobox'
import { makeArticle } from '../fixtures/article'
import { SourceType } from '../../types'
import type { InfoboxField, NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function field(key: string, label: string, value: string, group: string | null = null): InfoboxField {
  return { key, label, group, value, normalized_value: null, source: SourceType.Infobox }
}

describe('groupInfoboxFields', () => {
  test('подряд идущие поля одной группы объединяются, порядок сохраняется', () => {
    const blocks = groupInfoboxFields({
      capital: field('capital', 'Capital', 'Paris'),
      area_total: field('area_total', 'Total', '1', 'Area'),
      area_water: field('area_water', 'Water', '2', 'Area'),
      currency: field('currency', 'Currency', 'Euro'),
    })

    expect(blocks.map((b) => [b.group, b.fields.map((f) => f.key)])).toEqual([
      [null, ['capital']],
      ['Area', ['area_total', 'area_water']],
      [null, ['currency']],
    ])
  })

  test('пустой инфобокс - нет блоков', () => {
    expect(groupInfoboxFields({})).toEqual([])
  })
})

describe('infoboxWidget: контракт', () => {
  test('supports возвращает false для статьи без инфобокса', () => {
    expect(infoboxWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает true для статьи с инфобоксом', () => {
    const data = makeArticle({ infobox: { a: field('a', 'A', '1') } })
    expect(infoboxWidget.supports(data)).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(infoboxWidget)

    const selected = selectWidgets(loadFixture('socrates-ru.json'), registry)

    expect(selected.map((w) => w.id)).toEqual(['infobox-widget'])
  })
})

describe('infoboxWidget: отображение', () => {
  test('показывает пары «название — значение» (Сократ, ru)', () => {
    render(<infoboxWidget.render data={loadFixture('socrates-ru.json')} />)

    const label = screen.getByText('Место рождения')
    expect(label.tagName).toBe('DT')
    expect(label.nextElementSibling).toHaveTextContent('Афины')
  })

  test('по полю на каждую запись инфобокса', () => {
    const data = loadFixture('python.json')
    const { container } = render(<infoboxWidget.render data={data} />)

    expect(container.querySelectorAll('dt')).toHaveLength(Object.keys(data.infobox).length)
  })

  test('France: подзаголовки групп различают одинаковые подписи "Total"', () => {
    const data = loadFixture('france.json')
    render(<infoboxWidget.render data={data} />)

    const groups = screen.getAllByRole('heading', { level: 4 }).map((h) => h.textContent)
    expect(groups).toEqual(expect.arrayContaining(['Area', 'GDP (PPP)', 'GDP (nominal)']))
    expect(screen.getAllByText('Total').length).toBeGreaterThanOrEqual(2)
  })
})
