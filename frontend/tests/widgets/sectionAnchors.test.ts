import fs from 'node:fs'
import path from 'node:path'
import {
  flattenSections,
  computeAnchors,
  buildSectionUrl,
} from '../../lib/widgets/sectionAnchors'
import type { NormalizedArticleModel, Section } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function section(
  id: string,
  title: string,
  children: Section[] = [],
  level = 2
): Section {
  return { id, title, level, children }
}

describe('flattenSections', () => {
  test('обходит дерево в порядке документа (родитель перед детьми)', () => {
    const tree = [
      section('a', 'A', [section('a1', 'A1', [], 3), section('a2', 'A2', [], 3)]),
      section('b', 'B'),
    ]
    expect(flattenSections(tree).map((s) => s.id)).toEqual(['a', 'a1', 'a2', 'b'])
  })

  test('пустое дерево даёт пустой список', () => {
    expect(flattenSections([])).toEqual([])
  })

  test('порядок обхода совпадает с id из extractor (Токио)', () => {
    const data = loadFixture('tokyo-ru.json')
    const ids = flattenSections(data.sections).map((s) => s.id)
    expect(ids).toEqual(ids.map((_, index) => `section-${index}`))
  })
})

describe('computeAnchors', () => {
  test('пробелы заменяются на подчёркивания', () => {
    const anchors = computeAnchors([section('s0', 'Syntax and semantics')])
    expect(anchors.get('s0')).toBe('Syntax_and_semantics')
  })

  test('лишние пробелы по краям и внутри схлопываются', () => {
    const anchors = computeAnchors([section('s0', '  Two   spaces ')])
    expect(anchors.get('s0')).toBe('Two_spaces')
  })

  test('повторяющиеся заголовки получают суффиксы _2, _3', () => {
    const tree = [
      section('s0', 'Notes'),
      section('s1', 'Other'),
      section('s2', 'Notes'),
      section('s3', 'Notes'),
    ]
    const anchors = computeAnchors(tree)
    expect(anchors.get('s0')).toBe('Notes')
    expect(anchors.get('s1')).toBe('Other')
    expect(anchors.get('s2')).toBe('Notes_2')
    expect(anchors.get('s3')).toBe('Notes_3')
  })

  test('повторы считаются по порядку документа, в том числе между уровнями', () => {
    const tree = [section('s0', 'Notes', [section('s1', 'Notes', [], 3)])]
    const anchors = computeAnchors(tree)
    expect(anchors.get('s0')).toBe('Notes')
    expect(anchors.get('s1')).toBe('Notes_2')
  })

  test('на реальных статьях все якоря уникальны', () => {
    for (const filename of ['python.json', 'france.json', 'tokyo-ru.json']) {
      const data = loadFixture(filename)
      const anchors = computeAnchors(data.sections)
      expect(anchors.size).toBe(flattenSections(data.sections).length)
      expect(new Set(anchors.values()).size).toBe(anchors.size)
    }
  })
})

describe('buildSectionUrl', () => {
  const articleUrl = 'https://en.wikipedia.org/wiki/Python_(programming_language)'

  test('добавляет якорь к адресу статьи', () => {
    expect(buildSectionUrl(articleUrl, 'Syntax_and_semantics')).toBe(
      'https://en.wikipedia.org/wiki/Python_(programming_language)#Syntax_and_semantics'
    )
  })

  test('существующий фрагмент в адресе статьи отбрасывается', () => {
    expect(buildSectionUrl(articleUrl + '#History', 'Libraries')).toBe(
      'https://en.wikipedia.org/wiki/Python_(programming_language)#Libraries'
    )
  })

  test('кириллический якорь кодируется и декодируется обратно без потерь', () => {
    const url = buildSectionUrl('https://ru.wikipedia.org/wiki/Токио', 'История')
    const fragment = url.split('#')[1]
    expect(fragment).toMatch(/^[A-Za-z0-9%_.~-]+$/)
    expect(decodeURIComponent(fragment)).toBe('История')
  })

  test('служебные символы кодируются (& в названии раздела)', () => {
    const url = buildSectionUrl(articleUrl, 'Q&A')
    expect(url.split('#')[1]).toBe('Q%26A')
  })

  test('пустой якорь даёт адрес статьи без фрагмента', () => {
    expect(buildSectionUrl(articleUrl + '#Old', '')).toBe(articleUrl)
  })
})