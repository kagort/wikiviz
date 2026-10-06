import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { InfoBoxWidgetView } from '../../components/widgets/InfoBoxWidgetView'

/**
 * Widget-обёртка над InfoBoxWidgetView (Phase 6).
 */
function InfoBoxWidgetRoot({ data }: { data: NormalizedArticleModel }) {
  return <InfoBoxWidgetView infobox={data.infobox} />
}

export const infoboxWidget: Widget = {
  id: 'infobox-widget',
  name: 'InfoBox',
  version: '1.0.0',
  description: 'Отображает поля инфобокса статьи парами «название — значение»',
  supports: (data: NormalizedArticleModel) => Object.keys(data.infobox).length > 0,
  render: InfoBoxWidgetRoot,
}
