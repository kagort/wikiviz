'use client'

import type { NormalizedArticleModel } from '../../types'
import { widgetRegistry } from '../../lib/widgets/setup'
import { selectWidgets } from '../../lib/widgets/selector'

interface DevArticle {
  name: string
  data: NormalizedArticleModel
}

interface WidgetsDevClientProps {
  articles: DevArticle[]
}

/**
 * Служебная страница визуальной проверки: для каждой фикстуры
 * selectWidgets выбирает виджеты, затем они рисуются через widget.render.
 * Не для продакшена (см. техдолг: dev-страницы нужно закрыть до деплоя).
 */
export function WidgetsDevClient({ articles }: WidgetsDevClientProps) {
  return (
    <div style={{ padding: 20 }}>
      <h1>Все виджеты: визуальная проверка</h1>
      {articles.map(({ name, data }) => {
        const widgets = selectWidgets(data, widgetRegistry)
        return (
          <section key={name} style={{ marginTop: 48 }}>
            <h2>{data.article.title} ({name})</h2>
            <p>Выбраны виджеты: {widgets.map((w) => w.id).join(', ') || 'нет'}</p>
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