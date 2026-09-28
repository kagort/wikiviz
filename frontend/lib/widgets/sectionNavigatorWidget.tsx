import type { NormalizedArticleModel } from '../../types'
import type { Widget } from './types'
import { SectionNavigatorView } from '../../components/widgets/SectionNavigatorView'

/**
 * Widget-обёртка над SectionNavigatorView (Phase 6).
 */
function SectionNavigatorRoot({ data }: { data: NormalizedArticleModel }) {
  return <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
}

export const sectionNavigatorWidget: Widget = {
  id: 'section-navigator-widget',
  name: 'Section navigator',
  version: '1.0.0',
  description: 'Оглавление статьи со ссылками на разделы в Wikipedia',
  supports: (data: NormalizedArticleModel) => data.sections.length > 0,
  render: SectionNavigatorRoot,
}