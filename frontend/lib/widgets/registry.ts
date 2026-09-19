import type { Widget } from './types'

/**
 * WidgetRegistry — хранилище зарегистрированных виджетов.
 * Ничего не знает о конкретных виджетах (Rule 6 Roadmap):
 * работает только с контрактом Widget.
 */
export class WidgetRegistry {
  private widgets: Widget[] = []

  /** Добавляет виджет. Бросает ошибку, если виджет с таким id уже есть. */
  register(widget: Widget): void {
    if (this.widgets.some((w) => w.id === widget.id)) {
      throw new Error(`Widget with id "${widget.id}" is already registered`)
    }
    this.widgets.push(widget)
  }

  /** Возвращает виджет по id или undefined. */
  get(id: string): Widget | undefined {
    return this.widgets.find((w) => w.id === id)
  }

  /** Возвращает копию списка виджетов в порядке регистрации. */
  list(): Widget[] {
    return [...this.widgets]
  }
}

/** Единый реестр приложения. Тесты создают собственные экземпляры класса. */
export const widgetRegistry = new WidgetRegistry()