import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import type { NormalizedArticleModel, Section } from '../../types'
import { SectionNavigatorView } from '../../components/widgets/SectionNavigatorView'
import { flattenSections } from '../../lib/widgets/sectionAnchors'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function listDepth(element: HTMLElement): number {
  let depth = 0
  let current = element.parentElement
  while (current) {
    if (current.tagName === 'UL') depth++
    current = current.parentElement
  }
  return depth
}

describe('SectionNavigatorView', () => {
  test('показывает ссылку для каждого раздела дерева (Токио)', () => {
    const data = loadFixture('tokyo-ru.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    expect(screen.getAllByRole('link')).toHaveLength(
      flattenSections(data.sections).length
    )
  })

  test('вложенность отражает уровни заголовков (Токио: до четвёртого уровня)', () => {
    const data = loadFixture('tokyo-ru.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    const top = screen.getByRole('link', { name: 'Административно-территориальное деление' })
    const middle = screen.getByRole('link', { name: 'Западный Токио' })
    const deepest = screen.getByRole('link', { name: 'Города' })
    expect(listDepth(top)).toBe(1)
    expect(listDepth(middle)).toBe(2)
    expect(listDepth(deepest)).toBe(3)
  })

  test('ссылка ведёт на якорь раздела в статье (Python)', () => {
    const data = loadFixture('python.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    const link = screen.getByRole('link', { name: 'Syntax and semantics' })
    const base = data.article.url.split('#')[0]
    expect(link.getAttribute('href')).toBe(base + '#Syntax_and_semantics')
  })

  test('кириллический якорь кодируется и декодируется без потерь (Токио)', () => {
    const data = loadFixture('tokyo-ru.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    const href = screen.getByRole('link', { name: 'Западный Токио' }).getAttribute('href') ?? ''
    expect(decodeURIComponent(href.split('#')[1])).toBe('Западный_Токио')
  })

  test('все ссылки открываются в новой вкладке безопасно', () => {
    const data = loadFixture('python.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    for (const link of screen.getAllByRole('link')) {
      expect(link.getAttribute('target')).toBe('_blank')
      expect(link.getAttribute('rel')).toContain('noopener')
    }
  })

  test('повторяющиеся заголовки получают разные якоря по всему дереву', () => {
    const sections: Section[] = [
      { id: 's0', title: 'Notes', level: 2, children: [] },
      {
        id: 's1',
        title: 'Other',
        level: 2,
        children: [{ id: 's2', title: 'Notes', level: 3, children: [] }],
      },
    ]
    render(
      <SectionNavigatorView
        sections={sections}
        articleUrl="https://en.wikipedia.org/wiki/Test"
      />
    )
    const hrefs = screen.getAllByRole('link', { name: 'Notes' }).map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual([
      'https://en.wikipedia.org/wiki/Test#Notes',
      'https://en.wikipedia.org/wiki/Test#Notes_2',
    ])
  })

  test('пустой список разделов ничего не рендерит', () => {
    const { container } = render(
      <SectionNavigatorView sections={[]} articleUrl="https://en.wikipedia.org/wiki/Test" />
    )
    expect(container).toBeEmptyDOMElement()
  })

  test('оглавление доступно как навигационная область', () => {
    const data = loadFixture('python.json')
    render(
      <SectionNavigatorView sections={data.sections} articleUrl={data.article.url} />
    )
    expect(screen.getByRole('navigation', { name: 'Содержание статьи' })).toBeInTheDocument()
  })
})