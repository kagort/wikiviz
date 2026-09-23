import type { Table } from '../../types'

interface TableWidgetViewProps {
  table: Table
}

/**
 * Отображает одну таблицу (Phase 6, шаг 1 - только просмотр).
 * Сортировка, поиск, пагинация - следующие шаги.
 */
export function TableWidgetView({ table }: TableWidgetViewProps) {
  return (
    <div>
      {table.title && <h3>{table.title}</h3>}
      <table>
        <thead>
          <tr>
            {table.columns.map((column, index) => (
              <th key={index}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}