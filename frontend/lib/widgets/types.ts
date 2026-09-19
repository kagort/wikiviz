import type { ComponentType } from 'react'
import type { NormalizedArticleModel } from '../../types'

/**
 * WidgetSchema — «паспорт» виджета: статические метаданные.
 * Не содержит логики, только описание.
 */
export interface WidgetSchema {
  id: string
  name: string
  version: string
  description: string
}

/** Что получает компонент виджета: нормализованные данные статьи (не HTML Wikipedia, ТЗ §43). */
export interface WidgetProps {
  data: NormalizedArticleModel
}

/**
 * Widget — контракт, который реализует каждая визуализация.
 *
 * supports — умеет ли виджет показать эти данные (например, есть ли таблицы).
 * render   — React-КОМПОНЕНТ, а не функция: так внутри виджета
 *            можно использовать состояние (сортировка, поиск и т.п.).
 *            Использование: <widget.render data={data} />
 */
export interface Widget extends WidgetSchema {
  supports(data: NormalizedArticleModel): boolean
  render: ComponentType<WidgetProps>
}