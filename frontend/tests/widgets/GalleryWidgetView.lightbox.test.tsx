import fs from 'node:fs'
import path from 'node:path'
import { render, screen, fireEvent, within } from '@testing-library/react'
import type { NormalizedArticleModel } from '../../types'
import { GalleryWidgetView } from '../../components/widgets/GalleryWidgetView'

function loadFixture(filename: string): NormalizedArticleModel {
  const filePath = path.join(__dirname, '../fixtures/real', filename)
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
}

function getPreviewButtons() {
  return screen.getAllByRole('button', { name: /Открыть изображение/ })
}

describe('GalleryWidgetView: lightbox', () => {
  test('без клика lightbox не отображается', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('клик по превью открывает lightbox с полноразмерным изображением', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])

    const dialog = screen.getByRole('dialog')
    const img = within(dialog).getByRole('img')
    expect(img.getAttribute('src')).toBe(data.images[0].url)
  })

  test('кнопка "Закрыть" закрывает lightbox', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Закрыть' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('Escape закрывает lightbox', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('"Вперёд" переключает на следующее изображение', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    fireEvent.click(screen.getByRole('button', { name: 'Следующее изображение' }))

    const img = within(screen.getByRole('dialog')).getByRole('img')
    expect(img.getAttribute('src')).toBe(data.images[1].url)
  })

  test('"Вперёд" на последнем изображении зацикливается на первое', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    const buttons = getPreviewButtons()
    fireEvent.click(buttons[buttons.length - 1])
    fireEvent.click(screen.getByRole('button', { name: 'Следующее изображение' }))

    const img = within(screen.getByRole('dialog')).getByRole('img')
    expect(img.getAttribute('src')).toBe(data.images[0].url)
  })

  test('"Назад" на первом изображении зацикливается на последнее', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    fireEvent.click(screen.getByRole('button', { name: 'Предыдущее изображение' }))

    const img = within(screen.getByRole('dialog')).getByRole('img')
    expect(img.getAttribute('src')).toBe(data.images[data.images.length - 1].url)
  })

  test('стрелка вправо (клавиатура) переключает на следующее изображение', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'ArrowRight' })

    const img = within(screen.getByRole('dialog')).getByRole('img')
    expect(img.getAttribute('src')).toBe(data.images[1].url)
  })

  test('подпись в lightbox совпадает с caption изображения', () => {
    const data = loadFixture('tokyo-ru.json')
    render(<GalleryWidgetView images={data.images} />)

    fireEvent.click(getPreviewButtons()[0])
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText(data.images[0].caption as string)).toBeInTheDocument()
  })
})