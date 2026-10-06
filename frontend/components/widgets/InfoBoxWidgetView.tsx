import type { InfoboxField } from '../../types'
import { groupInfoboxFields } from '../../lib/widgets/infobox'

interface InfoBoxWidgetViewProps {
  infobox: Record<string, InfoboxField>
}

/**
 * Карточка инфобокса (Phase 6): пары «название — значение» в порядке
 * строк инфобокса; перед полями группы ("Area", "Статистика") -
 * подзаголовок. Группировка - в lib/widgets/infobox.ts.
 */
export function InfoBoxWidgetView({ infobox }: InfoBoxWidgetViewProps) {
  const blocks = groupInfoboxFields(infobox)
  if (blocks.length === 0) return null

  return (
    <div aria-label="Карточка статьи">
      {blocks.map((block, index) => (
        <div key={`${block.group ?? ''}-${index}`}>
          {block.group && <h4>{block.group}</h4>}
          <dl>
            {block.fields.map((field) => (
              <div key={field.key}>
                <dt>{field.label}</dt>
                <dd>{field.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </div>
  )
}
