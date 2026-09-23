import type { Location } from '../../types'

export interface SinglePointView {
  kind: 'single'
  center: [number, number]
  zoom: number
}

export interface BoundsView {
  kind: 'bounds'
  bounds: [[number, number], [number, number]] // [[southWest], [northEast]]
}

export type MapView = SinglePointView | BoundsView | null

/**
 * Вычисляет, как расположить карту для данного набора точек:
 * - null для пустого списка (вызывающий код не должен рендерить карту в этом случае,
 *   но функция не падает даже если это произошло);
 * - фиксированный центр и zoom для одной точки (bounding box из одной точки
 *   не даёт Leaflet разумного масштаба);
 * - bounding box (юго-западный и северо-восточный углы) для нескольких точек -
 *   Leaflet сам впишет его в видимую область через fitBounds.
 */
export function computeMapView(locations: Location[]): MapView {
  if (locations.length === 0) return null

  if (locations.length === 1) {
    return {
      kind: 'single',
      center: [locations[0].latitude, locations[0].longitude],
      zoom: 10,
    }
  }

  const latitudes = locations.map((l) => l.latitude)
  const longitudes = locations.map((l) => l.longitude)

  return {
    kind: 'bounds',
    bounds: [
      [Math.min(...latitudes), Math.min(...longitudes)],
      [Math.max(...latitudes), Math.max(...longitudes)],
    ],
  }
}

/**
 * Текст попапа для маркера. name может дублироваться у разных точек
 * (обнаружено на реальной статье France: два маркера с name="France" -
 * центр страны и Париж) - поэтому всегда добавляем координаты,
 * они уникальны и снимают неоднозначность.
 */
export function formatPopupText(location: Location): string {
  const coords = `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`
  const parts = [location.name]
  if (location.description) parts.push(location.description)
  parts.push(coords)
  return parts.join(' - ')
}