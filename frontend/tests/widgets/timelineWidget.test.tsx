import fs from 'node:fs'
import path from 'node:path'
import { render, screen, within } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { timelineWidget } from '../../lib/widgets/timelineWidget'
import { makeArticle } from '../fixtures/article'
import { DatePrecision, SourceType } from '../../types'
import type { Event, NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function makeEvent(id: string, date: string): Event {
  return {
    id,
    date,
    date_precision: DatePrecision.Day,
    title: `Event ${id}`,
    description: null,
    source: SourceType.ArticleText,
    confidence: 0.6,
  }
}

describe('timelineWidget: контракт', () => {
  test('supports возвращает false для статьи без событий', () => {
    expect(timelineWidget.supports(makeArticle())).toBe(false)
  })

  test('supports возвращает false для одного события', () => {
    const data = makeArticle({ events: [makeEvent('a', '1900-01-01')] })
    expect(timelineWidget.supports(data)).toBe(false)
  })

  test('supports возвращает true для двух событий', () => {
    const data = makeArticle({
      events: [makeEvent('a', '1900-01-01'), makeEvent('b', '1950-01-01')],
    })
    expect(timelineWidget.supports(data)).toBe(true)
  })

  test('регистрируется и выбирается через selectWidgets на реальных данных', () => {
    const registry = new WidgetRegistry()
    registry.register(timelineWidget)

    const selected = selectWidgets(loadFixture('julius-caesar.json'), registry)

    expect(selected.map((w) => w.id)).toEqual(['timeline-widget'])
  })
})

describe('timelineWidget: отображение', () => {
  test('рендерит по пункту на каждое событие', () => {
    const data = loadFixture('python.json')
    render(<timelineWidget.render data={data} />)

    const list = screen.getByRole('list', { name: 'Хронология' })
    expect(within(list).getAllByRole('listitem')).toHaveLength(data.events.length)
  })

  test('Цезарь (en): даты до н. э. идут первыми и подписаны "BC"', () => {
    render(<timelineWidget.render data={loadFixture('julius-caesar.json')} />)

    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent(/^\d+ BC/)
    expect(items[0]).not.toHaveTextContent(/^\d+ до н\. э\./)
  })

  test('Сократ (ru): даты до н. э. подписаны "до н. э." по возрастанию', () => {
    render(<timelineWidget.render data={loadFixture('socrates-ru.json')} />)

    const dates = screen
      .getAllByRole('listitem')
      .map((item) => item.querySelector('strong')?.textContent)
    expect(dates.length).toBeGreaterThanOrEqual(2)
    for (const date of dates) expect(date).toMatch(/^\d+ до н\. э\.$/)
    const years = dates.map((date) => Number(date?.split(' ')[0]))
    expect(years).toEqual([...years].sort((a, b) => b - a))
  })

  test('показывает источник и уверенность', () => {
    const data = makeArticle({
      events: [makeEvent('a', '1900-01-01'), makeEvent('b', '1950-01-01')],
    })
    render(<timelineWidget.render data={data} />)

    expect(screen.getAllByText('(текст статьи, 60%)')).toHaveLength(2)
  })
})
