import type { ChartGroup } from '../../lib/widgets/statistics'
import { barWidths, formatValue } from '../../lib/widgets/statistics'

interface StatisticsChartViewProps {
  groups: ChartGroup[]
}

// Один ряд данных - один цвет, легенда не нужна (заголовок называет ряд).
const BAR_COLOR = '#3b6ea8'

/**
 * Горизонтальные столбики без библиотеки (решение владельца, этап 6).
 * Каждая диаграмма - таблица «подпись | столбик | значение»: она же
 * табличный вид для доступности; подсказка при наведении - title строки.
 * Логика отбора групп и длины столбиков - в lib/widgets/statistics.ts.
 */
export function StatisticsChartView({ groups }: StatisticsChartViewProps) {
  if (groups.length === 0) return null

  return (
    <div>
      {groups.map((group) => {
        const widths = barWidths(group.items)
        return (
          <table key={group.title} aria-label={group.title}>
            <caption>{group.title}</caption>
            <tbody>
              {group.items.map((item, index) => {
                const value = formatValue(item.value, group.unit)
                return (
                  <tr key={`${item.label}-${index}`} title={`${item.label}: ${value}`}>
                    <th scope="row" style={{ textAlign: 'left', fontWeight: 'normal', paddingRight: 8 }}>
                      {item.label}
                    </th>
                    <td style={{ width: 300 }}>
                      <div
                        data-testid="bar"
                        style={{
                          width: `${widths[index]}%`,
                          height: 12,
                          background: BAR_COLOR,
                          borderRadius: '0 4px 4px 0',
                        }}
                      />
                    </td>
                    <td style={{ textAlign: 'right' }}>{value}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )
      })}
    </div>
  )
}
