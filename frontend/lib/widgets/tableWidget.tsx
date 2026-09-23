import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { TableWidgetView } from '../../components/widgets/TableWidgetView'

/**
 * Widget-обёртка над TableWidgetView (Phase 6).
 * render получает всю статью и отрисовывает TableWidgetView
 * для каждой найденной таблицы - у статьи их может быть несколько
 * (например, Токио: климат + население).
 */
function TableWidgetRoot({ data }: { data: NormalizedArticleModel }) {
  return (
    <div>
      {data.tables.map((table) => (
        <TableWidgetView key={table.id} table={table} />
      ))}
    </div>
  )
}

export const tableWidget: Widget = {
  id: 'table-widget',
  name: 'Table',
  version: '1.0.0',
  description: 'Отображает таблицы статьи с сортировкой, поиском и пагинацией',
  supports: (data: NormalizedArticleModel) => data.tables.length > 0,
  render: TableWidgetRoot,
}