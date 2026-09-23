import fs from 'node:fs'
import path from 'node:path'
import type { NormalizedArticleModel } from '../../../types'
import { MapDevClient } from '../../../components/dev/MapDevClient'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(process.cwd(), 'tests', 'fixtures', 'real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

/**
 * Служебная dev-страница для визуальной проверки MapWidget -
 * Leaflet не тестируется юнит-тестами, см. Phase 6 контекст-документ.
 * Не для продакшена, удалить или защитить перед деплоем.
 *
 * Server Component: читает фикстуры через fs и передаёт данные
 * в MapDevClient (Client Component), где уже подключается dynamic
 * import с ssr:false - в App Router это разрешено только внутри
 * Client Component.
 */
export default function MapDevPage() {
  const france = loadFixture('france.json')
  const tokyo = loadFixture('tokyo-ru.json')

  return (
    <MapDevClient
      franceLocations={france.locations}
      tokyoLocations={tokyo.locations}
    />
  )
}