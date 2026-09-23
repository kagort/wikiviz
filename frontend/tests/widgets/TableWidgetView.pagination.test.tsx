import { render, screen, fireEvent, within } from '@testing-library/react'
import type { Table } from '../../types'
import { SourceType } from '../../types'
import { TableWidgetView } from '../../components/widgets/TableWidgetView'

function makeTableWithRows(count: number): Table {
  return {
    id: 'test-table',
    title: null,
    columns: ['№'],
    rows: Array.from({ length: count }, (_, i) => [`Строка ${i + 1}`]),
    source: SourceType.Table,
  }
}

function getVisibleRowLabels(): string[] {
  const rows = screen.getAllByRole('row').slice(1)
  return rows.map((row) => within(row).getAllByRole('cell')[0].textContent ?? '')
}

describe('TableWidgetView: пагинация', () => {
  test('таблица с 10 строками и меньше - без элементов пагинации', () => {
    render(<TableWidgetView table={makeTableWithRows(10)} />)
    expect(screen.queryByText(/Страница/)).not.toBeInTheDocument()
  })

  test('таблица с 25 строками показывает первые 10 и элементы навигации', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    expect(getVisibleRowLabels()).toHaveLength(10)
    expect(screen.getByText('Строка 1')).toBeInTheDocument()
    expect(screen.queryByText('Строка 11')).not.toBeInTheDocument()
    expect(screen.getByText(/Страница 1 из 3/)).toBeInTheDocument()
  })

  test('кнопка "Вперёд" переключает страницу', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }))
    expect(screen.getByText('Строка 11')).toBeInTheDocument()
    expect(screen.queryByText('Строка 1')).not.toBeInTheDocument()
    expect(screen.getByText(/Страница 2 из 3/)).toBeInTheDocument()
  })

  test('кнопка "Назад" отключена на первой странице', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    expect(screen.getByRole('button', { name: 'Назад' })).toBeDisabled()
  })

  test('кнопка "Вперёд" отключена на последней странице', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }))
    fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }))
    expect(screen.getByText(/Страница 3 из 3/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Вперёд' })).toBeDisabled()
  })

  test('поиск сбрасывает страницу на первую', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }))
    expect(screen.getByText(/Страница 2 из 3/)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Поиск по таблице'), {
      target: { value: 'Строка 2' },
    })
    // "Строка 2", "Строка 20"..."Строка 25" - 7 совпадений, меньше PAGE_SIZE
    expect(screen.queryByText(/Страница/)).not.toBeInTheDocument()
    expect(screen.getByText('Строка 2')).toBeInTheDocument()
  })

  test('клик на сортировку сбрасывает страницу на первую', () => {
    render(<TableWidgetView table={makeTableWithRows(25)} />)
    fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }))
    fireEvent.click(screen.getByRole('button', { name: /№/ }))
    expect(screen.getByText(/Страница 1 из 3/)).toBeInTheDocument()
  })
})