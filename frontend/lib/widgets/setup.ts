import { widgetRegistry } from './registry'
import { tableWidget } from './tableWidget'
import { galleryWidget } from './galleryWidget'

/**
 * Точка сборки: здесь регистрируются все настоящие виджеты приложения.
 * Новый виджет подключается одной строкой - без изменений в registry.ts
 * или selector.ts (Rule 6 Roadmap).
 */
widgetRegistry.register(tableWidget)
widgetRegistry.register(galleryWidget)

export { widgetRegistry }