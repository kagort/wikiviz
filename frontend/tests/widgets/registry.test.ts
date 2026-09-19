import { WidgetRegistry } from '../../lib/widgets/registry'
import { makeDummyWidget } from '../helpers/dummyWidget'

describe('WidgetRegistry', () => {
  test('зарегистрированный виджет можно получить по id', () => {
    const registry = new WidgetRegistry()
    const widget = makeDummyWidget('a')
    registry.register(widget)
    expect(registry.get('a')).toBe(widget)
  })

  test('get для неизвестного id возвращает undefined', () => {
    const registry = new WidgetRegistry()
    expect(registry.get('nope')).toBeUndefined()
  })

  test('повторная регистрация того же id вызывает ошибку', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('a'))
    expect(() => registry.register(makeDummyWidget('a'))).toThrow(
      'already registered'
    )
  })

  test('list возвращает виджеты в порядке регистрации', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('first'))
    registry.register(makeDummyWidget('second'))
    registry.register(makeDummyWidget('third'))
    expect(registry.list().map((w) => w.id)).toEqual([
      'first',
      'second',
      'third',
    ])
  })

  test('list возвращает копию: изменение результата не портит реестр', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('a'))
    registry.list().pop()
    expect(registry.list()).toHaveLength(1)
  })

  test('разные экземпляры реестра независимы', () => {
    const r1 = new WidgetRegistry()
    const r2 = new WidgetRegistry()
    r1.register(makeDummyWidget('a'))
    expect(r2.list()).toHaveLength(0)
  })
})