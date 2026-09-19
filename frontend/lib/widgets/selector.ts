import type { NormalizedArticleModel } from '../../types'
import type { Widget } from './types'
import type { WidgetRegistry } from './registry'

/**
 * Возвращает виджеты, которые умеют показать данные статьи,
 * в порядке регистрации. Простая версия Phase 5;
 * rule engine появится в Phase 7 без изменения контракта Widget.
 *
 * Если supports() виджета бросает исключение, виджет пропускается,
 * остальные продолжают работать.
 */
export function selectWidgets(
  data: NormalizedArticleModel,
  registry: WidgetRegistry
): Widget[] {
  return registry.list().filter((widget) => {
    try {
      return widget.supports(data)
    } catch (error) {
      console.error(`Widget "${widget.id}": supports() failed`, error)
      return false
    }
  })
}