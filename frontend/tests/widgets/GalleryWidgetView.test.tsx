import fs from 'node:fs'
import path from 'node:path'
import { render, screen } from '@testing-library/react'
import type { NormalizedArticleModel, Image } from '../../types'
import { SourceType } from '../../types'
import { GalleryWidgetView } from '../../components/widgets/GalleryWidgetView'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

describe('GalleryWidgetView', () => {
  test('отображает превью для каждого изображения (Токио: 3 картинки)', () => {
    const data = loadFixture('tokyo-ru.json')
    const { container } = render(<GalleryWidgetView images={data.images} />)
    const imgs = container.querySelectorAll('img')
    expect(imgs).toHaveLength(3)
    expect(imgs[0].src).toBe(data.images[0].thumbnail_url)
  })

  test('подпись отображается, если caption есть', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)
    expect(
      screen.getByText('Токийский противопаводковый коллектор - крупнейшее в мире подземное противопаводковое инженерное сооружение')
    ).toBeInTheDocument()
  })

  test('alt берётся из caption, если собственного alt нет', () => {
    const data = loadFixture('tokyo-ru.json')
    const { container } = render(<GalleryWidgetView images={data.images} />)
    expect(container.querySelectorAll('img')[0].alt).toBe(data.images[0].caption)
  })

  test('и caption, и alt равны null (Python) - alt становится пустой строкой, без сбоя', () => {
    const data = loadFixture('python.json')
    const { container } = render(<GalleryWidgetView images={data.images} />)
    const img = container.querySelector('img')
    expect(img?.alt).toBe('')
    expect(screen.queryByRole('figure')?.querySelector('figcaption')).toBeNull()
  })

  test('url и thumbnail_url могут совпадать (Токио, второе изображение) - рендер не падает', () => {
    const data = loadFixture('tokyo-ru.json')
    const image = data.images[1]
    expect(image.url).toBe(image.thumbnail_url)
    const { container } = render(<GalleryWidgetView images={[image]} />)
    expect(container.querySelector('img')?.src).toBe(image.thumbnail_url)
  })

  test('thumbnail_url = null - используется url как fallback', () => {
    const image: Image = {
      url: 'https://example.org/full.jpg',
      thumbnail_url: null,
      caption: null,
      alt: null,
      source: SourceType.ArticleText,
    }
    const { container } = render(<GalleryWidgetView images={[image]} />)
    expect(container.querySelector('img')?.src).toBe(image.url)
  })

  test('пустой список изображений рендерится без ошибок', () => {
    const { container } = render(<GalleryWidgetView images={[]} />)
    expect(container.querySelectorAll('figure')).toHaveLength(0)
  })
})