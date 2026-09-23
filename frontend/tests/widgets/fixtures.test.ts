import fs from 'node:fs'
import path from 'node:path'
import type { NormalizedArticleModel } from '../../types'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  const raw = fs.readFileSync(filePath, 'utf-8')
  return JSON.parse(raw) as NormalizedArticleModel
}

describe('реальные фикстуры Wikipedia', () => {
  test('python.json загружается и содержит ожидаемые поля', () => {
    const data = loadFixture('python.json')
    expect(data.article.title).toContain('Python')
    expect(data.sections.length).toBeGreaterThan(0)
    expect(data.tables.length).toBeGreaterThan(0)
  })

  test('france.json загружается, локации и числа на месте', () => {
    const data = loadFixture('france.json')
    expect(data.article.title).toBe('France')
    expect(data.locations.length).toBeGreaterThan(0)
    expect(data.numbers.length).toBeGreaterThan(0)
  })

  test('tokyo-ru.json загружается с кириллицей без искажений', () => {
    const data = loadFixture('tokyo-ru.json')
    expect(data.article.title).toBe('Токио')
    expect(data.article.language).toBe('ru')
    expect(data.tables.length).toBeGreaterThan(0)
  })
})