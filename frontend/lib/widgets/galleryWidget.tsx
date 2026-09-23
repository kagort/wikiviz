import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { GalleryWidgetView } from '../../components/widgets/GalleryWidgetView'

/**
 * Widget-обёртка над GalleryWidgetView (Phase 6).
 */
function GalleryWidgetRoot({ data }: { data: NormalizedArticleModel }) {
  return <GalleryWidgetView images={data.images} />
}

export const galleryWidget: Widget = {
  id: 'gallery-widget',
  name: 'Gallery',
  version: '1.0.0',
  description: 'Отображает изображения статьи в виде сетки превью с lightbox',
  supports: (data: NormalizedArticleModel) => data.images.length > 0,
  render: GalleryWidgetRoot,
}