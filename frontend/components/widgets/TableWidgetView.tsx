'use client'

import { useState } from 'react'
import type { Table } from '../../types'

interface TableWidgetViewProps {
  table: Table
}

type SortDirection = 'asc' | 'desc'

interface SortState {
  columnIndex: number
  direction: SortDirection
}

/**
 * Отображает одну таблицу с сортировкой по клику на заголовок
 * и текстовым поиском по всем ячейкам строки.
 *
 * Сортировка строковая (localeCompare), не числовая - см. комментарий
 * ниже и Phase 6 контекст-документ (осознанное ограничение MVP).
 */
export function TableWidgetView({ table }: TableWidgetViewProps) {
  const [sort, setSort] = useState<SortState | null>(null)
  const [query, setQuery] = useState('')

  function handleHeaderClick(columnIndex: number) {
    setSort((current) => {
      if (current?.columnIndex === columnIndex) {
        return {
          columnIndex,
          direction: current.direction === 'asc' ? 'desc' : 'asc',
        }
      }
      return { columnIndex, direction: 'asc' }
    })
  }

  const normalizedQuery = query.trim().toLowerCase()
  const filteredRows = normalizedQuery
    ? table.rows.filter((row) =>
        row.some((cell) => cell.toLowerCase().includes(normalizedQuery))
      )
    : table.rows

  const displayedRows = sort
    ? [...filteredRows].sort((a, b) => {
        const left = a[sort.columnIndex] ?? ''
        const right = b[sort.columnIndex] ?? ''
        const result = left.localeCompare(right)
        return sort.direction === 'asc' ? result : -result
      })
    : filteredRows

  return (
    <div>
      {table.title && <h3>{table.title}</h3>}
      <input
        type="text"
        placeholder="Поиск по таблице"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        aria-label="Поиск по таблице"
      />
      <table>
        <thead>
          <tr>
            {table.columns.map((column, index) => {
              const isActive = sort?.columnIndex === index
              const indicator = isActive
                ? sort.direction === 'asc'
                  ? ' \u25B2'
                  : ' \u25BC'
                : ''
              return (
                <th key={index}>
                  <button type="button" onClick={() => handleHeaderClick(index)}>
                    {column}
                    {indicator}
                  </button>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {displayedRows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {displayedRows.length === 0 && <p>Ничего не найдено</p>}
    </div>
  )
}