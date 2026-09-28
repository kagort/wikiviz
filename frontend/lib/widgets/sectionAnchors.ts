import type { Section } from '../../types'

/**
 * Обход дерева разделов в порядке документа (родитель перед детьми).
 * Совпадает с порядком id "section-N", которые задаёт backend
 * (section_normalizer), а значит и с порядком заголовков в статье.
 */
export function flattenSections(sections: Section[]): Section[] {
  const result: Section[] = []
  for (const section of sections) {
    result.push(section)
    result.push(...flattenSections(section.children))
  }
  return result
}

function baseAnchor(title: string): string {
  return title.trim().replace(/\s+/g, '_')
}

/**
 * Сопоставляет id раздела и якорь Wikipedia. Пробелы заменяются на "_",
 * повторяющиеся заголовки получают суффикс _2, _3 в порядке документа
 * (так якоря строит MediaWiki).
 */
export function computeAnchors(sections: Section[]): Map<string, string> {
  const seen = new Map<string, number>()
  const anchors = new Map<string, string>()
  for (const section of flattenSections(sections)) {
    const base = baseAnchor(section.title)
    const count = (seen.get(base) ?? 0) + 1
    seen.set(base, count)
    anchors.set(section.id, count === 1 ? base : `${base}_${count}`)
  }
  return anchors
}

/**
 * Ссылка на раздел в статье Wikipedia. Уже существующий фрагмент (#...)
 * в адресе статьи отбрасывается, якорь кодируется (кириллица, & и т.п.):
 * браузеры сами декодируют процентное кодирование при поиске элемента.
 */
export function buildSectionUrl(articleUrl: string, anchor: string): string {
  const base = articleUrl.split('#')[0]
  if (!anchor) return base
  return `${base}#${encodeURIComponent(anchor)}`
}