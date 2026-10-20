'use client'

import { useEffect, useState } from 'react'
import {
  EMPTY_LABELS,
  countMarked,
  setMark,
  toggleGolden,
} from '../../lib/dev/reviewLabels'
import type { Mark, ReviewArticle, ReviewLabels, ReviewValue, SampleValue } from '../../lib/dev/reviewLabels'

const API = '/api/dev/review-labels'

const KIND_NAMES: Record<string, string> = {
  event: 'Дата',
  number: 'Число',
  table: 'Таблица',
  infobox_field: 'Инфобокс',
  image: 'Изображение',
  location: 'Координаты',
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
      style={{ fontWeight: current === mark ? 'bold' : 'normal' }}
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

/**
 * Страница разметки (docs/SELECTION_TZ.md, В5-В6):
 * - «Выборка»: ~100 показанных значений, отметка «верно / мусор» -> точность;
 * - «Статьи»: все значения статьи корпуса с причинами отбора, ★ - «золотой»
 *   факт, который обязан остаться.
 * Каждое изменение сразу сохраняется в backend/tests/corpus/review/labels.json.
 */
export function ReviewDevClient({ articles, sample }: ReviewDevClientProps) {
  const [labels, setLabels] = useState<ReviewLabels>(EMPTY_LABELS)
  const [status, setStatus] = useState('загрузка разметки…')
  const [tab, setTab] = useState<'sample' | 'articles'>('sample')
  const [file, setFile] = useState(articles[0]?.file ?? '')

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
  const article = articles.find((a) => a.file === file)
  const articlesWithGolden = articles.filter((a) => a.values.some((v) => labels.golden.includes(v.key))).length

  return (
    <div style={{ padding: 20 }}>
      <h1>Разметка отбора надёжных данных</h1>
      <p>
        Выборка: размечено {countMarked(sample.map((v) => v.key), labels)} из {sample.length}. Золотых фактов:{' '}
        {labels.golden.length} в {articlesWithGolden} статьях (цель — 3–5 фактов в 10–15 статьях).{' '}
        <span role="status">{status}</span>
      </p>
      <p>
        <button type="button" aria-pressed={tab === 'sample'} onClick={() => setTab('sample')}>
          Выборка
        </button>{' '}
        <button type="button" aria-pressed={tab === 'articles'} onClick={() => setTab('articles')}>
          Статьи
        </button>
      </p>

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

      {tab === 'articles' && (
        <>
          <label>
            Статья:{' '}
            <select value={file} onChange={(event) => setFile(event.target.value)}>
              {articles.map((a) => (
                <option key={a.file} value={a.file}>
                  {a.title} ({a.kind})
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
            <ul aria-label="Значения статьи">
              {article.values.map((value) => {
                const golden = labels.golden.includes(value.key)
                return (
                  <li key={value.key} style={{ marginBottom: 8, opacity: value.selected ? 1 : 0.6 }}>
                    <button
                      type="button"
                      aria-pressed={golden}
                      aria-label={golden ? 'Убрать из золотых' : 'Отметить как золотой факт'}
                      onClick={() => save(toggleGolden(labels, value.key))}
                    >
                      {golden ? '★' : '☆'}
                    </button>{' '}
                    <b>{KIND_NAMES[value.kind] ?? value.kind}</b>{' '}
                    {value.selected ? '· показано' : `· отброшено: ${value.rule} — ${value.reason}`}
                    <div>
                      <ValueText value={value} />
                    </div>
                    <MarkButtons value={value} labels={labels} onMark={onMark} />
                  </li>
                )
              })}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
