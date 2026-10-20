import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { TimelineWidgetView } from '../../components/widgets/TimelineWidgetView'


/**
 * Widget-обёртка над TimelineWidgetView (Phase 6).
 */
function TimelineWidgetRoot({ data }: { data: NormalizedArticleModel }) {
  return <TimelineWidgetView events={data.events} language={data.article.language} />
}

export const timelineWidget: Widget = {
  id: 'timeline-widget',
  name: 'Timeline',
  version: '1.0.0',
  description: 'Отображает события статьи списком по возрастанию даты',
  // Минимум в 2 события (решение владельца) проверяет отбор надёжных данных
  // на backend (правило EV-MIN): виджет получает либо хронологию, либо ничего.
  supports: (data: NormalizedArticleModel) => data.events.length > 0,
  render: TimelineWidgetRoot,
}
