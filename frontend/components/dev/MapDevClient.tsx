'use client'

import dynamic from 'next/dynamic'
import type { Location } from '../../types'

const MapWidgetView = dynamic(
  () => import('../widgets/MapWidgetView').then((m) => m.MapWidgetView),
  { ssr: false }
)

interface MapDevClientProps {
  franceLocations: Location[]
  tokyoLocations: Location[]
}

export function MapDevClient({ franceLocations, tokyoLocations }: MapDevClientProps) {
  return (
    <div style={{ padding: 20 }}>
      <h1>MapWidget: визуальная проверка</h1>

      <h2>France (2 точки, разный name/description - должен различаться попап)</h2>
      <MapWidgetView locations={franceLocations} />

      <h2 style={{ marginTop: 40 }}>Токио (1 точка)</h2>
      <MapWidgetView locations={tokyoLocations} />
    </div>
  )
}