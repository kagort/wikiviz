import type { Widget } from '../../lib/widgets/types'

/** Создаёт тестовый виджет-манекен. supports по умолчанию всегда true. */
export function makeDummyWidget(
  id: string,
  supports: Widget['supports'] = () => true
): Widget {
  return {
    id,
    name: `Dummy ${id}`,
    version: '1.0.0',
    description: 'Тестовый виджет',
    supports,
    render: () => <div>Dummy {id}</div>,
  }
}