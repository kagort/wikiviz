import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { TimelineWidgetView } from '../../components/widgets/TimelineWidgetView'

/** Минимум событий для шкалы: одна дата - ещё не хронология (решение владельца). */
export const MIN_TIMELINE_EVENTS = 2

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
  supports: (data: NormalizedArticleModel) => data.events.length >= MIN_TIMELINE_EVENTS,
  render: TimelineWidgetRoot,
}
