import fs from 'node:fs'
import path from 'node:path'
import type { SelectionResult } from '../../../types'
import { WidgetsDevClient } from '../../../components/dev/WidgetsDevClient'

const FIXTURES = [
  'python.json',
  'france.json',
  'tokyo-ru.json',
  'julius-caesar.json',
  'socrates-ru.json',
]

function loadSelection(filename: string): SelectionResult {
  // Результат отбора надёжных данных (backend: python -m scripts.apply_selection).
  const filePath = path.join(process.cwd(), 'tests', 'fixtures', 'real', 'selection', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

/**
 * Server Component: читает результаты отбора через fs и передаёт в
 * Client Component отобранные данные (их получат виджеты) и сводку
 * отброшенного. Служебная страница, не для продакшена.
 */
export default function WidgetsDevPage() {
  const articles = FIXTURES.map((name) => {
    const { selected, rejected } = loadSelection(name)
    return { name, data: selected, rejected }
  })
  return <WidgetsDevClient articles={articles} />
}
