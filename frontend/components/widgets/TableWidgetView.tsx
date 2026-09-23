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
 * Отображает одну таблицу с сортировкой по клику на заголовок.
 *
 * Сортировка строковая (localeCompare), не числовая: например,
 * "9" будет идти после "10". Числовой парсинг локализованных форматов
 * ("3 699 428", "31,6%") - осознанно отложенная задача будущего
 * transformer/NLP-слоя (по аналогии с NumberExtractor, ТЗ §17.3),
 * а не логика виджета - см. Phase 6 контекст-документ.
 */
export function TableWidgetView({ table }: TableWidgetViewProps) {
  const [sort, setSort] = useState<SortState | null>(null)

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

  const displayedRows = sort
    ? [...table.rows].sort((a, b) => {
        const left = a[sort.columnIndex] ?? ''
        const right = b[sort.columnIndex] ?? ''
        const result = left.localeCompare(right)
        return sort.direction === 'asc' ? result : -result
      })
    : table.rows

  return (
    <div>
      {table.title && <h3>{table.title}</h3>}
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
    </div>
  )
}