import fs from 'node:fs'
import path from 'node:path'
import { render, screen, fireEvent, within } from '@testing-library/react'
import type { NormalizedArticleModel, Table } from '../../types'
import { SourceType } from '../../types'
import { TableWidgetView } from '../../components/widgets/TableWidgetView'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

// Небольшая таблица с заведомо известным порядком - для проверки
// корректности самой сортировки, независимо от содержимого фикстур.
const sortTestTable: Table = {
  id: 'test-table',
  title: null,
  columns: ['Имя', 'Значение'],
  rows: [
    ['Вишня', '10'],
    ['Абрикос', '9'],
    ['Банан', '2'],
  ],
  source: SourceType.Table,
}

function getColumnCells(columnIndex: number): string[] {
  const rows = screen.getAllByRole('row').slice(1) // без строки заголовка
  return rows.map(
    (row) => within(row).getAllByRole('cell')[columnIndex].textContent ?? ''
  )
}

describe('TableWidgetView: сортировка', () => {
  test('до клика строки идут в исходном порядке', () => {
    render(<TableWidgetView table={sortTestTable} />)
    expect(getColumnCells(0)).toEqual(['Вишня', 'Абрикос', 'Банан'])
  })

  test('клик на заголовок сортирует по возрастанию (строковый порядок)', () => {
    render(<TableWidgetView table={sortTestTable} />)
    fireEvent.click(screen.getByRole('button', { name: /Имя/ }))
    expect(getColumnCells(0)).toEqual(['Абрикос', 'Банан', 'Вишня'])
  })

  test('повторный клик на тот же заголовок переключает на убывание', () => {
    render(<TableWidgetView table={sortTestTable} />)
    const header = screen.getByRole('button', { name: /Имя/ })
    fireEvent.click(header)
    fireEvent.click(header)
    expect(getColumnCells(0)).toEqual(['Вишня', 'Банан', 'Абрикос'])
  })

  test('строковая сортировка не числовая: "10" идёт перед "2"', () => {
    render(<TableWidgetView table={sortTestTable} />)
    fireEvent.click(screen.getByRole('button', { name: /Значение/ }))
    // "10" < "2" как строки, хотя 10 > 2 как числа - это осознанное
    // ограничение MVP (числовой парсинг - задача будущего transformer'а)
    expect(getColumnCells(1)).toEqual(['10', '2', '9'])
  })

  test('клик на другой заголовок сортирует по новому столбцу, начиная с возрастания', () => {
    render(<TableWidgetView table={sortTestTable} />)
    fireEvent.click(screen.getByRole('button', { name: /Имя/ }))
    fireEvent.click(screen.getByRole('button', { name: /Значение/ }))
    expect(getColumnCells(1)).toEqual(['10', '2', '9'])
  })

  test('сортировка на реальных данных (Токио, климат) не падает', () => {
    const data = loadFixture('tokyo-ru.json')
    const table = data.tables[0]
    render(<TableWidgetView table={table} />)
    fireEvent.click(screen.getByRole('button', { name: /Показатель/ }))
    expect(getColumnCells(0).length).toBe(table.rows.length)
  })
})