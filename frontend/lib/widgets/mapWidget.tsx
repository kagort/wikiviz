'use client'

import dynamic from 'next/dynamic'
import type { NormalizedArticleModel } from '../../types'
import type { Widget } from './types'

// ssr:false обязателен: Leaflet обращается к window при инициализации карты
// и падает при попытке серверного рендера (см. Phase 6 контекст-документ,
// раздел MapWidget - та же проблема, что и на dev-странице /dev/map).
const MapWidgetView = dynamic(
  () => import('../../components/widgets/MapWidgetView').then((m) => m.MapWidgetView),
  { ssr: false }
)

/**
 * Widget-обёртка над MapWidgetView (Phase 6).
 */
function MapWidgetRoot({ data }: { data: NormalizedArticleModel }) {
  return <MapWidgetView locations={data.locations} />
}

export const mapWidget: Widget = {
  id: 'map-widget',
  name: 'Map',
  version: '1.0.0',
  description: 'Отображает координаты статьи на интерактивной карте',
  supports: (data: NormalizedArticleModel) => data.locations.length > 0,
  render: MapWidgetRoot,
}