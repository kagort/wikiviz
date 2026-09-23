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
    const data = loadFixture('tokyo-ru.json')
    const table = data.tables[1] // title: null

    render(<TableWidgetView table={table} />)

    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
})