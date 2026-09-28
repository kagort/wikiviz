import fs from 'node:fs'
import path from 'node:path'
import type { NormalizedArticleModel } from '../../../types'
import { WidgetsDevClient } from '../../../components/dev/WidgetsDevClient'

const FIXTURES = [
  'python.json',
  'france.json',
  'tokyo-ru.json',
  'julius-caesar.json',
  'socrates-ru.json',
]

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(process.cwd(), 'tests', 'fixtures', 'real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

/**
 * Server Component: читает фикстуры через fs и передаёт данные
 * в Client Component (данные сериализуемы, функции виджетов остаются
 * на стороне клиента). Служебная страница, не для продакшена.
 */
export default function WidgetsDevPage() {
  const articles = FIXTURES.map((name) => ({ name, data: loadFixture(name) }))
  return <WidgetsDevClient articles={articles} />
}