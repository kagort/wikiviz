import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import type { Widget } from '../../lib/widgets/types'
import { makeDummyWidget } from '../helpers/dummyWidget'
import { makeArticle } from '../fixtures/article'

/** Виджет с внутренним состоянием: доказывает, что render может использовать hooks. */
function CounterComponent() {
  const [count, setCount] = useState(0)
  return (
    <button onClick={() => setCount(count + 1)}>Clicks: {count}</button>
  )
}

const counterWidget: Widget = {
  id: 'counter',
  name: 'Counter',
  version: '1.0.0',
  description: 'Тестовый виджет с состоянием',
  supports: () => true,
  render: CounterComponent,
}

/** Виджет, который читает данные статьи из props. */
const titleWidget: Widget = {
  id: 'title',
  name: 'Title',
  version: '1.0.0',
  description: 'Показывает заголовок статьи',
  supports: () => true,
  render: ({ data }) => <h1>{data.article.title}</h1>,
}

describe('Widget Framework: регистрация -> выбор -> рендер', () => {
  test('выбранные виджеты отрисовываются через <widget.render />', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('a'))
    registry.register(titleWidget)
    const data = makeArticle()

    const selected = selectWidgets(data, registry)

    render(
      <div>
        {selected.map((w) => (
          <w.render key={w.id} data={data} />
        ))}
      </div>
    )

    expect(screen.getByText('Dummy a')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test' })).toBeInTheDocument()
  })

  test('виджет получает данные статьи через props', () => {
    const registry = new WidgetRegistry()
    registry.register(titleWidget)
    const data = makeArticle({
      article: {
        id: 2,
        title: 'Python',
        language: 'en',
        url: 'https://en.wikipedia.org/wiki/Python',
        description: null,
        summary: null,
      },
    })

    const [widget] = selectWidgets(data, registry)
    render(<widget.render data={data} />)

    expect(screen.getByRole('heading', { name: 'Python' })).toBeInTheDocument()
  })

  test('внутри виджета работает состояние (useState)', () => {
    const registry = new WidgetRegistry()
    registry.register(counterWidget)
    const data = makeArticle()

    const [widget] = selectWidgets(data, registry)
    render(<widget.render data={data} />)

    const button = screen.getByRole('button', { name: 'Clicks: 0' })
    fireEvent.click(button)
    fireEvent.click(button)
    expect(
      screen.getByRole('button', { name: 'Clicks: 2' })
    ).toBeInTheDocument()
  })

  test('новый виджет подключается регистрацией, без правок реестра и селектора', () => {
    const registry = new WidgetRegistry()
    const data = makeArticle()
    expect(selectWidgets(data, registry)).toHaveLength(0)

    registry.register(counterWidget)
    expect(selectWidgets(data, registry).map((w) => w.id)).toEqual(['counter'])
  })
})