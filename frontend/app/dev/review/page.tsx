import fs from 'node:fs'
import path from 'node:path'
import type { ReviewArticle, SampleValue } from '../../../lib/dev/reviewLabels'
import { ReviewDevClient } from '../../../components/dev/ReviewDevClient'

const REVIEW_DIR = path.join(process.cwd(), '..', 'backend', 'tests', 'corpus', 'review')

function load<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(REVIEW_DIR, name), 'utf-8'))
}

/**
 * Разметка владельца для оценки отбора надёжных данных (docs/SELECTION_TZ.md,
 * В5-В6). Данные готовит backend: python -m scripts.apply_selection.
 * Служебная страница, не для продакшена.
 */
export default function ReviewDevPage() {
  return (
    <ReviewDevClient
      articles={load<ReviewArticle[]>('articles.json')}
      sample={load<SampleValue[]>('sample.json')}
    />
  )
}
