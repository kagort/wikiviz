import fs from 'node:fs/promises'
import path from 'node:path'
import { EMPTY_LABELS, parseLabels } from '../../../../lib/dev/reviewLabels'

/**
 * Чтение и сохранение разметки владельца для /dev/review.
 * Пишет файл в репозиторий (backend/tests/corpus/review/labels.json),
 * поэтому работает только в режиме разработки (npm run dev).
 */
const LABELS_PATH = path.join(process.cwd(), '..', 'backend', 'tests', 'corpus', 'review', 'labels.json')

function devOnly(): Response | null {
  return process.env.NODE_ENV === 'development'
    ? null
    : Response.json({ error: 'only in development' }, { status: 403 })
}

export async function GET() {
  const denied = devOnly()
  if (denied) return denied
  try {
    return Response.json(parseLabels(JSON.parse(await fs.readFile(LABELS_PATH, 'utf-8'))))
  } catch {
    return Response.json(EMPTY_LABELS)
  }
}

export async function POST(request: Request) {
  const denied = devOnly()
  if (denied) return denied
  let labels
  try {
    labels = parseLabels(await request.json())
  } catch (error) {
    return Response.json({ error: (error as Error).message }, { status: 400 })
  }
  await fs.writeFile(LABELS_PATH, JSON.stringify(labels, null, 1) + '\n', 'utf-8')
  return Response.json(labels)
}
