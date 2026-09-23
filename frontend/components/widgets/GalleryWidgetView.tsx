'use client'

import { useState } from 'react'
import type { Image } from '../../types'

interface GalleryWidgetViewProps {
  images: Image[]
}

/**
 * Сетка превью изображений с lightbox (Phase 6).
 *
 * thumbnail_url может быть null по контракту (extractor не всегда
 * находит превью-версию) - fallback на url (полноразмерную версию).
 * alt обязателен для <img> по доступности, но caption и alt в данных
 * независимы и оба могут быть null (обнаружено на реальных статьях,
 * см. Phase 6 контекст-документ) - fallback: alt ?? caption ?? ''.
 */
export function GalleryWidgetView({ images }: GalleryWidgetViewProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  function close() {
    setOpenIndex(null)
  }

  function showPrevious() {
    setOpenIndex((current) => {
      if (current === null) return current
      return (current - 1 + images.length) % images.length
    })
  }

  function showNext() {
    setOpenIndex((current) => {
      if (current === null) return current
      return (current + 1) % images.length
    })
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'Escape') close()
    if (event.key === 'ArrowLeft') showPrevious()
    if (event.key === 'ArrowRight') showNext()
  }

  const openImage = openIndex !== null ? images[openIndex] : null

  return (
    <div>
      <div>
        {images.map((image, index) => (
          <figure key={index}>
            <button
              type="button"
              onClick={() => setOpenIndex(index)}
              aria-label={`Открыть изображение ${index + 1} из ${images.length}`}
            >
              <img
                src={image.thumbnail_url ?? image.url}
                alt={image.alt ?? image.caption ?? ''}
              />
            </button>
            {image.caption && <figcaption>{image.caption}</figcaption>}
          </figure>
        ))}
      </div>

      {openImage && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Просмотр изображения"
          onKeyDown={handleKeyDown}
        >
          <button type="button" onClick={close} aria-label="Закрыть">
            Закрыть
          </button>
          <button type="button" onClick={showPrevious} aria-label="Предыдущее изображение">
            Назад
          </button>
          <img
            src={openImage.url}
            alt={openImage.alt ?? openImage.caption ?? ''}
          />
          <button type="button" onClick={showNext} aria-label="Следующее изображение">
            Вперёд
          </button>
          {openImage.caption && <p>{openImage.caption}</p>}
        </div>
      )}
    </div>
  )
}