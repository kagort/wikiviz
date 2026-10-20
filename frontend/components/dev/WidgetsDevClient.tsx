'use client'

import type { NormalizedArticleModel, RejectedValue } from '../../types'
import { widgetRegistry } from '../../lib/widgets/setup'
import { selectWidgets } from '../../lib/widgets/selector'

interface DevArticle {
  name: string
  data: NormalizedArticleModel
  rejected: RejectedValue[]
}

/** "EV-LIST ×173, IMG-MAX ×27" - сводка правил отбора по убыванию. */
function rejectedSummary(rejected: RejectedValue[]): string {
  const counts = new Map<string, number>()
  for (const item of rejected) counts.set(item.rule, (counts.get(item.rule) ?? 0) + 1)
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([rule, count]) => `${rule} ×${count}`)
    .join(', ')
}

interface WidgetsDevClientProps {
  articles: DevArticle[]
}

/**
 * Служебная страница визуальной проверки: для каждой фикстуры
 * selectWidgets выбирает виджеты по отобранным данным, затем они
 * рисуются через widget.render; под заголовком - сводка отброшенного.
 * Не для продакшена (см. техдолг: dev-страницы нужно закрыть до деплоя).
 */
export function WidgetsDevClient({ articles }: WidgetsDevClientProps) {
  return (
    <div style={{ padding: 20 }}>
      <h1>Все виджеты: визуальная проверка</h1>
      {articles.map(({ name, data, rejected }) => {
        const widgets = selectWidgets(data, widgetRegistry)
        return (
          <section key={name} style={{ marginTop: 48 }}>
            <h2>{data.article.title} ({name})</h2>
            <p>Выбраны виджеты: {widgets.map((w) => w.id).join(', ') || 'нет'}</p>
            <p>
              Отброшено отбором: {rejected.length}
              {rejected.length > 0 && ` (${rejectedSummary(rejected)})`}
            </p>
            {widgets.map((w) => (
              <div key={w.id} style={{ marginTop: 24, borderTop: '1px solid #999' }}>
                <h3>{w.name}</h3>
                <w.render data={data} />
              </div>
            ))}
          </section>
        )
      })}
    </div>
  )
}