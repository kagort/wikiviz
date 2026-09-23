import { widgetRegistry } from '../../lib/widgets/setup'

describe('lib/widgets/setup: сборка виджетов приложения', () => {
  test('tableWidget зарегистрирован в глобальном реестре', () => {
    expect(widgetRegistry.get('table-widget')).toBeDefined()
  })

  test('galleryWidget зарегистрирован в глобальном реестре', () => {
    expect(widgetRegistry.get('gallery-widget')).toBeDefined()
  })

  test('mapWidget зарегистрирован в глобальном реестре', () => {
    expect(widgetRegistry.get('map-widget')).toBeDefined()
  })
})