'use client'

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Location } from '../../types'
import { computeMapView, formatPopupText } from '../../lib/widgets/mapGeometry'

// Известная проблема Leaflet + бандлеры (webpack/Turbopack): иконки маркеров
// по умолчанию ссылаются на пути, которые ломаются при сборке - маркер
// отображается пустым прямоугольником без изображения. Стандартный обход -
// явно переопределить Icon.Default на CDN-ссылки.
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

interface MapWidgetViewProps {
  locations: Location[]
}

/**
 * Отображает координаты статьи на карте (react-leaflet).
 *
 * Вся содержательная логика (расчёт центра/масштаба, текст попапа)
 * вынесена в lib/widgets/mapGeometry.ts и протестирована отдельно -
 * сам Leaflet не тестируется юнит-тестами (не работает в jsdom),
 * только визуальной проверкой в браузере. См. Phase 6 контекст-документ.
 */
export function MapWidgetView({ locations }: MapWidgetViewProps) {
  const view = computeMapView(locations)
  if (!view) return null

  const mapProps =
    view.kind === 'single'
      ? { center: view.center, zoom: view.zoom }
      : { bounds: view.bounds }

  return (
    <MapContainer
      {...mapProps}
      style={{ height: '400px', width: '100%' }}
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {locations.map((location) => (
        <Marker
          key={location.id}
          position={[location.latitude, location.longitude]}
          icon={defaultIcon}
        >
          <Popup>{formatPopupText(location)}</Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}