import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { ReviewDevClient } from '../../components/dev/ReviewDevClient'
import type { ReviewArticle, SampleValue } from '../../lib/dev/reviewLabels'

const shown = {
  key: 'pushkin-ru.json|event|1799-06-06|Дата рождения|infobox',
  kind: 'event',
  preview: '1799-06-06 — Дата рождения',
  selected: true,
  rule: null,
  reason: null,
  where: 'инфобокс',
}
const rejected = {
  key: 'pushkin-ru.json|event|1821-12-16|Ссылка|article_text',
  kind: 'event',
  preview: '1821-12-16 — Ссылка',
  selected: false,
  rule: 'EV-TEXT',
  reason: 'дата из текста статьи',
}
const controlValue = {
  key: 'random-ru-1.json|infobox_field|страна',
  kind: 'infobox_field',
  preview: 'Страна: Россия',
  selected: true,
  rule: null,
  reason: null,
}
const articles: ReviewArticle[] = [
  { file: 'london-en.json', kind: 'city', title: 'London', url: 'https://en.wikipedia.org/wiki/London', values: [] },
  { file: 'pushkin-ru.json', kind: 'person-modern', title: 'Пушкин', url: 'https://ru.wikipedia.org/wiki/x', values: [shown, rejected] },
  { file: 'random-ru-1.json', kind: 'random', title: 'Зельрайн', url: 'https://ru.wikipedia.org/wiki/y', values: [controlValue] },
]
const sample: SampleValue[] = [{ ...shown, article: 'Пушкин', file: 'pushkin-ru.json' }]

function mockFetch() {
  const calls: { method: string; body?: unknown }[] = []
  global.fetch = jest.fn((_url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ method: init?.method ?? 'GET', body: init?.body ? JSON.parse(String(init.body)) : undefined })
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ labels: {}, golden: [] }) } as Response)
  }) as jest.Mock
  return calls
}

async function renderPage() {
  const calls = mockFetch()
  render(<ReviewDevClient articles={articles} sample={sample} />)
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(''))
  return calls
}

describe('ReviewDevClient', () => {
  test('инструкция показывает три шага с прогрессом', async () => {
    await renderPage()

    const howTo = screen.getByRole('region', { name: 'Как размечать' })
    expect(howTo).toHaveTextContent('Размечено 0 из 1')
    expect(howTo).toHaveTextContent('Отмечено 0 фактов в 0 статьях из 10')
    expect(howTo).toHaveTextContent('Контрольная группа')
  })

  test('шаг 1: отметка в выборке сразу сохраняется', async () => {
    const calls = await renderPage()

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Верно' }))
    })

    expect(screen.getByRole('region', { name: 'Как размечать' })).toHaveTextContent('Размечено 1 из 1 ✓ готово')
    expect(calls.at(-1)).toEqual({ method: 'POST', body: { labels: { [shown.key]: 'ok' }, golden: [] } })
  })

  test('шаг 2: русские статьи первыми, кнопка «Обязательно оставить» ставит золотой факт', async () => {
    const calls = await renderPage()

    fireEvent.click(screen.getByRole('button', { name: '2. Золотые факты' }))
    expect(screen.getByRole('combobox')).toHaveValue('pushkin-ru.json')
    // Сначала показанные значения, ниже - отброшенные с правилом.
    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings).toEqual(['Показано на странице', 'Отброшено отбором'])
    expect(screen.getByText(/EV-TEXT — дата из текста статьи/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Верно' })).not.toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: '☆ Обязательно оставить' })[0])
    })

    expect(calls.at(-1)?.body).toEqual({ labels: {}, golden: [shown.key] })
    expect(screen.getByRole('button', { name: '★ Обязательно оставить' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Как размечать' })).toHaveTextContent('Отмечено 1 фактов в 1 статьях')
  })

  test('шаг 3: контрольная группа показывает показанные значения случайных статей', async () => {
    await renderPage()

    fireEvent.click(screen.getByRole('button', { name: '3. Контрольная группа' }))
    const group = screen.getByRole('region', { name: 'Зельрайн' })
    expect(within(group).getByText('Страна: Россия')).toBeInTheDocument()

    await act(async () => {
      fireEvent.click(within(group).getByRole('button', { name: 'Мусор' }))
    })
    expect(screen.getByRole('region', { name: 'Как размечать' })).toHaveTextContent('Размечено 1 из 1 ✓ готово.')
  })
})
