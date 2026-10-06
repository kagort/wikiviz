import type { InfoboxField } from '../../types'

export interface InfoboxBlock {
  group: string | null
  fields: InfoboxField[]
}

/**
 * Разбивает поля инфобокса на подряд идущие блоки с одинаковой группой,
 * сохраняя порядок полей (порядок ключей объекта = порядок строк
 * инфобокса; backend не даёт ключей из одних цифр, которые JavaScript
 * переставил бы в начало).
 */
export function groupInfoboxFields(infobox: Record<string, InfoboxField>): InfoboxBlock[] {
  const blocks: InfoboxBlock[] = []
  for (const field of Object.values(infobox)) {
    const group = field.group ?? null
    const last = blocks[blocks.length - 1]
    if (last && last.group === group) {
      last.fields.push(field)
    } else {
      blocks.push({ group, fields: [field] })
    }
  }
  return blocks
}
