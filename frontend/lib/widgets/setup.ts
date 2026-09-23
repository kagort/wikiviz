import { widgetRegistry } from './registry'
import { tableWidget } from './tableWidget'

/**
 * Точка сборки: здесь регистрируются все настоящие виджеты приложения.
 * Новый виджет подключается одной строкой - без изменений в registry.ts
 * или selector.ts (Rule 6 Roadmap).
 */
widgetRegistry.register(tableWidget)

export { widgetRegistry }