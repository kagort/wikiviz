import type { NormalizedArticleModel } from '../../types'

/**
 * Минимальная статья для тестов: все списки пусты.
 * Приведение через unknown сделано намеренно: фикстура нужна только
 * для проверки механики виджетов, а не формы каждой вложенной модели.
 */
export function makeArticle(
  overrides: Record<string, unknown> = {}
): NormalizedArticleModel {
  return {
    article: {
      id: 1,
      title: 'Test',
      language: 'en',
      url: 'https://en.wikipedia.org/wiki/Test',
      description: null,
      summary: null,
    },
    sections: [],
    infobox: {},
    tables: [],
    locations: [],
    events: [],
    numbers: [],
    people: [],
    organizations: [],
    works: [],
    relations: [],
    images: [],
    links: [],
    metadata: {},
    ...overrides,
  } as unknown as NormalizedArticleModel
}