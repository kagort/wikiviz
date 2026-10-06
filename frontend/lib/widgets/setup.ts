import { widgetRegistry } from './registry'
import { tableWidget } from './tableWidget'
import { galleryWidget } from './galleryWidget'
import { mapWidget } from './mapWidget'
import { sectionNavigatorWidget } from './sectionNavigatorWidget'
import { timelineWidget } from './timelineWidget'
import { infoboxWidget } from './infoboxWidget'
import { statisticsChartWidget } from './statisticsChartWidget'

/**
 * Точка сборки: здесь регистрируются все настоящие виджеты приложения.
 * Новый виджет подключается одной строкой - без изменений в registry.ts
 * или selector.ts (Rule 6 Roadmap).
 *
 * Порядок регистрации = порядок показа (selectWidgets сохраняет его).
 * Приоритеты появятся в Phase 7.
 */
widgetRegistry.register(tableWidget)
widgetRegistry.register(galleryWidget)
widgetRegistry.register(mapWidget)
widgetRegistry.register(sectionNavigatorWidget)
widgetRegistry.register(timelineWidget)
widgetRegistry.register(infoboxWidget)
widgetRegistry.register(statisticsChartWidget)

export { widgetRegistry }