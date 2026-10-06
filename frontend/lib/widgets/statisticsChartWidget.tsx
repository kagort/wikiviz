import type { NormalizedArticleModel } from '../../types'
import type { Widget } from '../../lib/widgets/types'
import { StatisticsChartView } from '../../components/widgets/StatisticsChartView'
import { findChartGroups } from './statistics'

/**
 * Widget-обёртка над StatisticsChartView (Phase 6).
 */
function StatisticsChartRoot({ data }: { data: NormalizedArticleModel }) {
  return <StatisticsChartView groups={findChartGroups(data.numbers)} />
}

export const statisticsChartWidget: Widget = {
  id: 'statistics-chart-widget',
  name: 'Statistics',
  version: '1.0.0',
  description: 'Столбчатая диаграмма групп процентных значений статьи',
  supports: (data: NormalizedArticleModel) => findChartGroups(data.numbers).length > 0,
  render: StatisticsChartRoot,
}
