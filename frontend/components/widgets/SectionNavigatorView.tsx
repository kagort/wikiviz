import type { Section } from '../../types'
import { computeAnchors, buildSectionUrl } from '../../lib/widgets/sectionAnchors'

interface SectionListProps {
  sections: Section[]
  articleUrl: string
  anchors: Map<string, string>
}

/** Рекурсивный список: раздел выводит свою ссылку, затем список своих детей. */
function SectionList({ sections, articleUrl, anchors }: SectionListProps) {
  return (
    <ul>
      {sections.map((section) => (
        <li key={section.id}>
          <a
            href={buildSectionUrl(articleUrl, anchors.get(section.id) ?? '')}
            target="_blank"
            rel="noopener noreferrer"
          >
            {section.title}
          </a>
          {section.children.length > 0 && (
            <SectionList
              sections={section.children}
              articleUrl={articleUrl}
              anchors={anchors}
            />
          )}
        </li>
      ))}
    </ul>
  )
}

interface SectionNavigatorViewProps {
  sections: Section[]
  articleUrl: string
}

/**
 * Оглавление статьи (Phase 6): вложенный список ссылок на разделы
 * в самой Wikipedia (новая вкладка). Все разделы показываются как есть,
 * служебные не скрываются - флаг на backend будет добавлен позже.
 *
 * Якоря считаются один раз для всего дерева: суффиксы _2, _3 у
 * повторяющихся заголовков зависят от порядка во всём документе.
 */
export function SectionNavigatorView({
  sections,
  articleUrl,
}: SectionNavigatorViewProps) {
  if (sections.length === 0) return null

  const anchors = computeAnchors(sections)

  return (
    <nav aria-label="Содержание статьи">
      <SectionList sections={sections} articleUrl={articleUrl} anchors={anchors} />
    </nav>
  )
}
