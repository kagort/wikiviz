import { render, screen } from '@testing-library/react'

test('Jest работает', () => {
  expect(1 + 1).toBe(2)
})

test('React-компонент отрисовывается в тесте', () => {
  render(<div>Привет, WikiViz</div>)
  expect(screen.getByText('Привет, WikiViz')).toBeInTheDocument()
})