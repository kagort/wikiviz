import fs from 'node:fs'
import path from 'node:path'
import { render, screen, within } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { statisticsChartWidget } from '../../lib/widgets/statisticsChartWidget'
import { findChartGroups, barWidths, formatValue } from '../../lib/widgets/statistics'
import { makeArticle } from '../fixtures/article'
import { SourceType } from '../../types'
import type { NormalizedArticleModel, NumericValue } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function num(label: string, value: number, unit: string | null = '%'): NumericValue {
  return { label, value, unit, year: null, source: SourceType.Infobox }
}

describe('findChartGroups', () => {
  test('группа из трёх и больше процентов с общим началом подписи', () => {
    const groups = findChartGroups([
      num('Religion — Christianity', 48),
      num('Religion — Islam', 7),
      num('Religion — Judaism', 1),
    ])

    expect(groups).toEqual([
      {
        title: 'Religion',
        unit: '%',
        items: [
          { label: 'Christianity', value: 48 },
          { label: 'Islam', value: 7 },
          { label: 'Judaism', value: 1 },
        ],
      },
    ])
  })

  test('меньше трёх значений - не диаграмма', () => {
    expect(findChartGroups([num('A — x', 1), num('A — y', 2)])).toEqual([])
  })

  test('разные единицы в группе - не диаграмма (Area: km² и %)', () => {
    expect(
      findChartGroups([
        num('Area — Total', 632702.3, 'km²'),
        num('Area — Water (%)', 0.86),
        num('Area — Metropolitan', 543941, 'km²'),
      ])
    ).toEqual([])
  })

  test('числа без группы в подписи не используются (годы Цезаря)', () => {
    expect(
      findChartGroups([num('Praetor', 62, 'BC'), num('Consul', 59, 'BC'), num('Dictator', 44, 'BC')])
    ).toEqual([])
  })

  test('France: только религии, все 10 значений', () => {
    const groups = findChartGroups(loadFixture('france.json').numbers)

    expect(groups.map((g) => g.title)).toEqual(['Religion (2025)'])
    expect(groups[0].items).toHaveLength(10)
  })

  test.each(['python.json', 'tokyo-ru.json', 'julius-caesar.json', 'socrates-ru.json'])(
    '%s: пригодных групп нет',
    (file) => {
      expect(findChartGroups(loadFixture(file).numbers)).toEqual([])
    }
  )
})

describe('barWidths и formatValue', () => {
  test('шкала процентов от 0 до 100', () => {
    expect(barWidths([{ label: 'a', value: 48 }, { label: 'b', value: 100 }])).toEqual([48, 100])
  })

  test('значения больше 100 растягивают шкалу до максимума', () => {
    expect(barWidths([{ label: 'a', value: 100 }, { label: 'b', value: 200 }])).toEqual([50, 100])
  })

  test('отрицательные значения не дают отрицательной ширины', () => {
    expect(barWidths([{ label: 'a', value: -5 }])).toEqual([0])
  })

  test('подпись значения', () => {
    expect(formatValue(48, '%')).toBe('48%')
    expect(formatValue(37.5, '%')).toBe('37.5%')
    expect(formatValue(1 / 3, '%')).toBe('0.33%')
  })
})

describe('statisticsChartWidget', () => {
  test('supports: false без пригодных групп, true для France', () => {
    expect(statisticsChartWidget.supports(makeArticle())).toBe(false)
    expect(statisticsChartWidget.supports(loadFixture('tokyo-ru.json'))).toBe(false)
    expect(statisticsChartWidget.supports(loadFixture('france.json'))).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(statisticsChartWidget)

    expect(selectWidgets(loadFixture('france.json'), registry).map((w) => w.id)).toEqual([
      'statistics-chart-widget',
    ])
  })

  test('France: таблица-диаграмма с подписью, 10 строк, значения и столбики', () => {
    render(<statisticsChartWidget.render data={loadFixture('france.json')} />)

    const table = screen.getByRole('table', { name: 'Religion (2025)' })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(10)
    expect(within(rows[0]).getByRole('rowheader')).toHaveTextContent('Christianity')
    expect(rows[0]).toHaveTextContent('48%')
    expect(rows[0]).toHaveAttribute('title', 'Christianity: 48%')
    expect(within(table).getAllByTestId('bar')[0]).toHaveStyle({ width: '48%' })
  })
})
