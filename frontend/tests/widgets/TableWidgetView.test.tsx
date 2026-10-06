import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import type { NormalizedArticleModel } from '../../types'
import { TableWidgetView } from '../../components/widgets/TableWidgetView'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('TableWidgetView', () => {
  test('отображает заголовки колонок и строки реальной таблицы (Python)', () => {
    const data = loadFixture('python.json')
    const table = data.tables[0]

    render(<TableWidgetView table={table} />)

    for (const column of table.columns) {
      expect(screen.getByText(column)).toBeInTheDocument()
    }
    expect(screen.getByText(table.rows[0][0])).toBeInTheDocument()
  })

  test('заголовок таблицы (caption) отображается, если он есть', () => {
    const data = loadFixture('tokyo-ru.json')
    const table = data.tables[0] // "Климат Токио"

    render(<TableWidgetView table={table} />)

    expect(screen.getByText('Климат Токио')).toBeInTheDocument()
  })

  test('таблица без title (caption=null) рендерится без заголовка', () => {
    // Таблица сражений Цезаря: подписи нет. (Таблица населения Токио
    // с этапа 7 получает название из пояснения над шапкой.)
    const data = loadFixture('julius-caesar.json')
    const table = data.tables[0]
    expect(table.title).toBeNull()

    render(<TableWidgetView table={table} />)

    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  test('примечания таблицы показываются под ней, а не строкой данных (Токио, климат)', () => {
    const data = loadFixture('tokyo-ru.json')
    const table = data.tables[0]

    render(<TableWidgetView table={table} />)

    const notes = screen.getByRole('list', { name: 'Примечания к таблице' })
    expect(notes).toHaveTextContent(/^Источник:/)
    const dataCells = screen.getAllByRole('cell').map((cell) => cell.textContent ?? '')
    expect(dataCells.some((text) => text.startsWith('Источник:'))).toBe(false)
  })

  test('без примечаний список примечаний не выводится', () => {
    const data = loadFixture('python.json')

    render(<TableWidgetView table={data.tables[0]} />)

    expect(screen.queryByRole('list', { name: 'Примечания к таблице' })).not.toBeInTheDocument()
  })

  test('многострочная шапка: колонки "Возраст — ..." (Токио, население)', () => {
    const data = loadFixture('tokyo-ru.json')
    const table = data.tables[1]

    render(<TableWidgetView table={table} />)

    expect(screen.getByRole('heading', { name: /^Статистика населения Токио/ })).toBeInTheDocument()
    expect(screen.getByText('Возраст — до 15')).toBeInTheDocument()
    expect(table.rows[0][0]).toMatch(/1920/)
  })
})
