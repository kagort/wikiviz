import type { Image } from '../../types'

interface GalleryWidgetViewProps {
  images: Image[]
}

/**
 * Сетка превью изображений (Phase 6, шаг 1). Lightbox - шаг 2.
 *
 * thumbnail_url может быть null по контракту (extractor не всегда
 * находит превью-версию) - fallback на url (полноразмерную версию).
 * alt обязателен для <img> по доступности, но caption и alt в данных
 * независимы и оба могут быть null (обнаружено на реальных статьях,
 * см. Phase 6 контекст-документ) - fallback: alt ?? caption ?? ''.
 */
export function GalleryWidgetView({ images }: GalleryWidgetViewProps) {
  return (
    <div>
      {images.map((image, index) => (
        <figure key={index}>
          <img
            src={image.thumbnail_url ?? image.url}
            alt={image.alt ?? image.caption ?? ''}
          />
          {image.caption && <figcaption>{image.caption}</figcaption>}
        </figure>
      ))}
    </div>
  )
}