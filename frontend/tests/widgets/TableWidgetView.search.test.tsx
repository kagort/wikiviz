import { render, screen, fireEvent, within } from '@testing-library/react'
import type { Table } from '../../types'
import { SourceType } from '../../types'
import { TableWidgetView } from '../../components/widgets/TableWidgetView'

const searchTestTable: Table = {
  id: 'test-table',
  title: null,
  columns: ['Имя', 'Город'],
  rows: [
    ['Иван', 'Москва'],
    ['Анна', 'Пятигорск'],
    ['Пётр', 'Москва'],
  ],
  source: SourceType.Table,
}

function getColumnCells(columnIndex: number): string[] {
  const rows = screen.getAllByRole('row').slice(1)
  return rows.map(
    (row) => within(row).getAllByRole('cell')[columnIndex].textContent ?? ''
  )
}

describe('TableWidgetView: поиск', () => {
  test('без запроса видны все строки', () => {
    render(<TableWidgetView table={searchTestTable} />)
    expect(getColumnCells(0)).toEqual(['Иван', 'Анна', 'Пётр'])
  })

  test('поиск фильтрует строки по совпадению в любой ячейке', () => {
    render(<TableWidgetView table={searchTestTable} />)
    fireEvent.change(screen.getByLabelText('Поиск по таблице'), {
      target: { value: 'Москва' },
    })
    expect(getColumnCells(0)).toEqual(['Иван', 'Пётр'])
  })

  test('поиск нечувствителен к регистру', () => {
    render(<TableWidgetView table={searchTestTable} />)
    fireEvent.change(screen.getByLabelText('Поиск по таблице'), {
      target: { value: 'москва' },
    })
    expect(getColumnCells(0)).toEqual(['Иван', 'Пётр'])
  })

  test('при отсутствии совпадений показывается сообщение', () => {
    render(<TableWidgetView table={searchTestTable} />)
    fireEvent.change(screen.getByLabelText('Поиск по таблице'), {
      target: { value: 'Токио' },
    })
    expect(screen.getByText('Ничего не найдено')).toBeInTheDocument()
    expect(screen.queryAllByRole('row')).toHaveLength(1) // только заголовок
  })

  test('поиск и сортировка работают вместе', () => {
    render(<TableWidgetView table={searchTestTable} />)
    fireEvent.change(screen.getByLabelText('Поиск по таблице'), {
      target: { value: 'Москва' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Имя/ }))
    expect(getColumnCells(0)).toEqual(['Иван', 'Пётр'])
  })
})