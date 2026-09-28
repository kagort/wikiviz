import type { Event } from '../../types'
import { sortEvents, formatEventDate, formatEventSource } from '../../lib/widgets/timeline'

interface TimelineWidgetViewProps {
  events: Event[]
  language: string
}

/**
 * Временная шкала (Phase 6): вертикальный список событий по возрастанию
 * даты. Дата подписывается по языку статьи ("44 BC" / "44 до н. э."),
 * рядом - источник и уверенность. Логика сортировки и подписей -
 * в lib/widgets/timeline.ts.
 */
export function TimelineWidgetView({ events, language }: TimelineWidgetViewProps) {
  if (events.length === 0) return null

  return (
    <ol aria-label="Хронология">
      {sortEvents(events).map((event, index) => (
        <li key={`${event.id}-${index}`}>
          <strong>{formatEventDate(event, language)}</strong>
          {' — '}
          {event.title}
          {event.description && <>: {event.description}</>}{' '}
          <small>({formatEventSource(event)})</small>
        </li>
      ))}
    </ol>
  )
}
