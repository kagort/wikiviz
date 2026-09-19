import { WidgetRegistry } from '../../lib/widgets/registry'
import { selectWidgets } from '../../lib/widgets/selector'
import { makeDummyWidget } from '../helpers/dummyWidget'
import { makeArticle } from '../fixtures/article'

describe('selectWidgets', () => {
  test('возвращает только виджеты, у которых supports вернул true', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('yes', () => true))
    registry.register(makeDummyWidget('no', () => false))
    const result = selectWidgets(makeArticle(), registry)
    expect(result.map((w) => w.id)).toEqual(['yes'])
  })

  test('сохраняет порядок регистрации', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('first'))
    registry.register(makeDummyWidget('second'))
    registry.register(makeDummyWidget('third'))
    const result = selectWidgets(makeArticle(), registry)
    expect(result.map((w) => w.id)).toEqual(['first', 'second', 'third'])
  })

  test('пустой реестр даёт пустой результат', () => {
    expect(selectWidgets(makeArticle(), new WidgetRegistry())).toEqual([])
  })

  test('если никто не подошёл, результат пуст (не ошибка)', () => {
    const registry = new WidgetRegistry()
    registry.register(makeDummyWidget('a', () => false))
    expect(selectWidgets(makeArticle(), registry)).toEqual([])
  })

  test('supports получает данные статьи: решение зависит от таблиц', () => {
    const registry = new WidgetRegistry()
    registry.register(
      makeDummyWidget('tables', (d) => d.tables.length > 0)
    )
    const empty = makeArticle()
    const withTable = makeArticle({ tables: [{}] })
    expect(selectWidgets(empty, registry)).toHaveLength(0)
    expect(selectWidgets(withTable, registry)).toHaveLength(1)
  })

  test('виджет с упавшим supports пропускается, остальные работают', () => {
    const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    const registry = new WidgetRegistry()
    registry.register(
      makeDummyWidget('broken', () => {
        throw new Error('boom')
      })
    )
    registry.register(makeDummyWidget('healthy'))
    const result = selectWidgets(makeArticle(), registry)
    expect(result.map((w) => w.id)).toEqual(['healthy'])
    expect(errorSpy).toHaveBeenCalledTimes(1)
    errorSpy.mockRestore()
  })
})