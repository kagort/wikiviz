'use client'

import { useEffect, useState } from 'react'
import type React from 'react'
import {
  EMPTY_LABELS,
  countMarked,
  setMark,
  toggleGolden,
} from '../../lib/dev/reviewLabels'
import type { Mark, ReviewArticle, ReviewLabels, ReviewValue, SampleValue } from '../../lib/dev/reviewLabels'

const API = '/api/dev/review-labels'
const CONTROL_KIND = 'random'
const GOLDEN_TARGET_ARTICLES = 10

/** Русскоязычные статьи, с которых удобно начать «золотые» факты (шаг 2). */
const GOLDEN_SUGGESTED = [
  'pushkin-ru.json',
  'gagarin-ru.json',
  'platon-ru.json',
  'germaniya-ru.json',
  'kazakhstan-ru.json',
  'sankt-peterburg-ru.json',
  'novosibirsk-ru.json',
  'war-1812-ru.json',
  'kulikovskaya-bitva-ru.json',
  'baikal-ru.json',
]

const KIND_NAMES: Record<string, string> = {
  event: 'Дата',
  number: 'Число',
  table: 'Таблица',
  infobox_field: 'Инфобокс',
  image: 'Изображение',
  location: 'Координаты',
}

type Tab = 'sample' | 'golden' | 'control'

/**
 * Явный вид кнопок: Tailwind (preflight) убирает у <button> рамку и фон,
 * и без стилей кнопки неотличимы от текста.
 */
function buttonStyle(pressed: boolean): React.CSSProperties {
  return {
    border: '1px solid #555',
    borderRadius: 4,
    padding: '2px 10px',
    margin: '2px 4px 2px 0',
    cursor: 'pointer',
    background: pressed ? '#2b6cb0' : '#f2f2f2',
    color: pressed ? '#fff' : '#111',
    fontWeight: pressed ? 'bold' : 'normal',
  }
}

interface ReviewDevClientProps {
  articles: ReviewArticle[]
  sample: SampleValue[]
}

interface MarkButtonsProps {
  value: ReviewValue
  labels: ReviewLabels
  onMark: (key: string, mark: Mark | null) => void
}

function MarkButtons({ value, labels, onMark }: MarkButtonsProps) {
  const current = labels.labels[value.key]
  const button = (mark: Mark, text: string) => (
    <button
      type="button"
      aria-pressed={current === mark}
      onClick={() => onMark(value.key, current === mark ? null : mark)}
      style={buttonStyle(current === mark)}
    >
      {current === mark ? `✓ ${text}` : text}
    </button>
  )
  return (
    <span>
      {button('ok', 'Верно')} {button('junk', 'Мусор')}
    </span>
  )
}

function ValueText({ value }: { value: ReviewValue }) {
  return (
    <>
      {value.thumbnail && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={value.thumbnail} alt="" style={{ maxHeight: 80, display: 'block' }} />
      )}
      <span>{value.preview}</span>
      {value.where && <small> ({value.where})</small>}
      {value.detail && <small> — {value.detail}</small>}
    </>
  )
}

interface GoldenListProps {
  values: ReviewValue[]
  labels: ReviewLabels
  onToggle: (key: string) => void
}

function GoldenList({ values, labels, onToggle }: GoldenListProps) {
  if (values.length === 0) return <p>— нет —</p>
  return (
    <ul>
      {values.map((value) => {
        const golden = labels.golden.includes(value.key)
        return (
          <li key={value.key} style={{ marginBottom: 8 }}>
            <button type="button" aria-pressed={golden} onClick={() => onToggle(value.key)} style={buttonStyle(golden)}>
              {golden ? '★ Обязательно оставить' : '☆ Обязательно оставить'}
            </button>{' '}
            <b>{KIND_NAMES[value.kind] ?? value.kind}</b>
            {!value.selected && ` · ${value.rule} — ${value.reason}`}
            <div>
              <ValueText value={value} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function done(ok: boolean) {
  return ok ? ' ✓ готово' : ''
}

/**
 * Страница разметки (docs/SELECTION_TZ.md, В5-В6) - три шага:
 * 1. «Выборка»: ~100 показанных значений, «Верно / Мусор» -> точность;
 * 2. «Золотые факты»: в 10 статьях по 3-5 фактов, которые обязаны остаться;
 * 3. «Контрольная группа»: показанные значения случайных статей, «Верно / Мусор».
 * Каждое изменение сразу сохраняется в backend/tests/corpus/review/labels.json.
 */
export function ReviewDevClient({ articles, sample }: ReviewDevClientProps) {
  const [labels, setLabels] = useState<ReviewLabels>(EMPTY_LABELS)
  const [status, setStatus] = useState('загрузка разметки…')
  const [tab, setTab] = useState<Tab>('sample')

  const goldenArticles = [
    ...GOLDEN_SUGGESTED.map((file) => articles.find((a) => a.file === file)).filter(
      (a): a is ReviewArticle => a !== undefined
    ),
    ...articles.filter((a) => a.kind !== CONTROL_KIND && !GOLDEN_SUGGESTED.includes(a.file)),
  ]
  const [file, setFile] = useState(goldenArticles[0]?.file ?? '')

  useEffect(() => {
    fetch(API)
      .then((response) => response.json())
      .then((data: ReviewLabels) => {
        setLabels(data)
        setStatus('')
      })
      .catch(() => setStatus('не удалось загрузить разметку'))
  }, [])

  function save(next: ReviewLabels) {
    setLabels(next)
    setStatus('сохранение…')
    fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(next) })
      .then((response) => setStatus(response.ok ? 'сохранено' : 'ошибка сохранения'))
      .catch(() => setStatus('ошибка сохранения'))
  }

  const onMark = (key: string, mark: Mark | null) => save(setMark(labels, key, mark))
  const onToggle = (key: string) => save(toggleGolden(labels, key))
  const goldenCount = (article: ReviewArticle) => article.values.filter((v) => labels.golden.includes(v.key)).length

  const sampleMarked = countMarked(sample.map((v) => v.key), labels)
  const articlesWithGolden = articles.filter((a) => goldenCount(a) > 0).length
  const controlArticles = articles.filter((a) => a.kind === CONTROL_KIND)
  const controlValues = controlArticles.flatMap((a) => a.values.filter((v) => v.selected))
  const controlMarked = countMarked(controlValues.map((v) => v.key), labels)
  const article = goldenArticles.find((a) => a.file === file)

  const tabButton = (value: Tab, text: string) => (
    <button
      type="button"
      aria-pressed={tab === value}
      onClick={() => setTab(value)}
      style={buttonStyle(tab === value)}
    >
      {text}
    </button>
  )

  return (
    <div style={{ padding: 20, maxWidth: 1000 }}>
      <h1>Разметка отбора надёжных данных</h1>

      <section aria-label="Как размечать">
        <p>Три шага. Каждый щелчок сохраняется сразу. <span role="status">{status}</span></p>
        <ol>
          <li>
            <b>Выборка:</b> у каждого значения нажать «Верно» или «Мусор». Размечено {sampleMarked} из{' '}
            {sample.length}
            {done(sampleMarked === sample.length)}.
          </li>
          <li>
            <b>Золотые факты:</b> выбрать статью и нажать «☆ Обязательно оставить» у 3–5 самых важных фактов
            (дата рождения, площадь, главная таблица, портрет…). Отмечено {labels.golden.length} фактов в{' '}
            {articlesWithGolden} статьях из {GOLDEN_TARGET_ARTICLES}
            {done(articlesWithGolden >= GOLDEN_TARGET_ARTICLES)}.
          </li>
          <li>
            <b>Контрольная группа:</b> у каждого значения шести случайных статей нажать «Верно» или «Мусор».
            Размечено {controlMarked} из {controlValues.length}
            {done(controlValues.length > 0 && controlMarked === controlValues.length)}.
          </li>
        </ol>
        <p>
          {tabButton('sample', '1. Выборка')} {tabButton('golden', '2. Золотые факты')}{' '}
          {tabButton('control', '3. Контрольная группа')}
        </p>
      </section>

      {tab === 'sample' && (
        <ol aria-label="Выборка для оценки точности">
          {sample.map((value) => (
            <li key={value.key} style={{ marginBottom: 12 }}>
              <div>
                <b>{KIND_NAMES[value.kind] ?? value.kind}</b> · {value.article}
              </div>
              <ValueText value={value} />
              <div>
                <MarkButtons value={value} labels={labels} onMark={onMark} />
              </div>
            </li>
          ))}
        </ol>
      )}

      {tab === 'golden' && (
        <>
          <p>
            Отметьте 3–5 фактов, без которых страница о статье теряет смысл. Сначала показаны значения, которые
            видны на странице, ниже — отброшенные отбором.
          </p>
          <label>
            Статья:{' '}
            <select value={file} onChange={(event) => setFile(event.target.value)}>
              {goldenArticles.map((a) => (
                <option key={a.file} value={a.file}>
                  {a.title}
                  {goldenCount(a) > 0 ? ` — отмечено ${goldenCount(a)}` : ''}
                </option>
              ))}
            </select>
          </label>{' '}
          {article && (
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              открыть в Wikipedia
            </a>
          )}
          {article && (
            <>
              <h2>Показано на странице</h2>
              <GoldenList values={article.values.filter((v) => v.selected)} labels={labels} onToggle={onToggle} />
              <h2>Отброшено отбором</h2>
              <p>Звёздочка здесь означает: правило ошибается, этот факт нужно показывать.</p>
              <GoldenList values={article.values.filter((v) => !v.selected)} labels={labels} onToggle={onToggle} />
            </>
          )}
        </>
      )}

      {tab === 'control' && (
        <>
          <p>Случайные статьи, на которых правила не настраивались. Размечаются только показанные значения.</p>
          {controlArticles.map((a) => (
            <section key={a.file} aria-label={a.title}>
              <h2>
                {a.title}{' '}
                <small>
                  <a href={a.url} target="_blank" rel="noopener noreferrer">
                    открыть в Wikipedia
                  </a>
                </small>
              </h2>
              <ol>
                {a.values
                  .filter((v) => v.selected)
                  .map((value) => (
                    <li key={value.key} style={{ marginBottom: 10 }}>
                      <b>{KIND_NAMES[value.kind] ?? value.kind}</b> <ValueText value={value} />
                      <div>
                        <MarkButtons value={value} labels={labels} onMark={onMark} />
                      </div>
                    </li>
                  ))}
              </ol>
            </section>
          ))}
        </>
      )}
    </div>
  )
}
