import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ReviewDevClient } from '../../components/dev/ReviewDevClient'
import type { ReviewArticle, SampleValue } from '../../lib/dev/reviewLabels'

const value = {
  key: 'a.json|event|1961-04-12|History|article_text',
  kind: 'event',
  preview: '1961-04-12 — History',
  selected: true,
  rule: null,
  reason: null,
  where: 'абзац, History',
}
const rejected = {
  key: 'a.json|event|1961-04-14|Awards|article_text',
  kind: 'event',
  preview: '1961-04-14 — Awards',
  selected: false,
  rule: 'EV-LIST',
  reason: 'дата из пункта списка, а не из рассказа',
}
const articles: ReviewArticle[] = [
  { file: 'a.json', kind: 'person-modern', title: 'Гагарин', url: 'https://ru.wikipedia.org/wiki/x', values: [value, rejected] },
]
const sample: SampleValue[] = [{ ...value, article: 'Гагарин', file: 'a.json' }]

function mockFetch() {
  const calls: { method: string; body?: unknown }[] = []
  global.fetch = jest.fn((_url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ method: init?.method ?? 'GET', body: init?.body ? JSON.parse(String(init.body)) : undefined })
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ labels: {}, golden: [] }) } as Response)
  }) as jest.Mock
  return calls
}

describe('ReviewDevClient', () => {
  test('отметка в выборке сразу сохраняется и меняет счётчик', async () => {
    const calls = mockFetch()
    render(<ReviewDevClient articles={articles} sample={sample} />)
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(''))

    expect(screen.getByText(/размечено 0 из 1/)).toBeInTheDocument()
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Верно' }))
    })

    expect(screen.getByText(/размечено 1 из 1/)).toBeInTheDocument()
    expect(calls.at(-1)).toEqual({ method: 'POST', body: { labels: { [value.key]: 'ok' }, golden: [] } })
  })

  test('во вкладке «Статьи» видна причина отбрасывания, ★ отмечает золотой факт', async () => {
    const calls = mockFetch()
    render(<ReviewDevClient articles={articles} sample={sample} />)
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(''))

    fireEvent.click(screen.getByRole('button', { name: 'Статьи' }))
    expect(screen.getByText(/отброшено: EV-LIST — дата из пункта списка/)).toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getAllByRole('button', { name: 'Отметить как золотой факт' })[0])
    })
    expect(calls.at(-1)?.body).toEqual({ labels: {}, golden: [value.key] })
    expect(screen.getByText(/Золотых фактов: 1 в 1 статьях/)).toBeInTheDocument()
  })
})
