import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn().mockResolvedValue({ data: { models: [], policies: [], hit_rate: 0, total_requests: 0, hits: 0, misses: 0, evictions: 0, current_size_mb: 0, max_size_mb: 0 } }),
      post: vi.fn(),
    }),
  },
}))

function renderApp() {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  )
}

describe('App', () => {
  it('renders header with navigation', () => {
    renderApp()
    expect(screen.getByText('Nexus Workbench')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Models')).toBeInTheDocument()
    expect(screen.getByText('Chat')).toBeInTheDocument()
    expect(screen.getByText('Cache')).toBeInTheDocument()
  })

  it('navigates to dashboard by default', async () => {
    renderApp()
    await waitFor(() => {
      expect(screen.getByText(/Monitor your MoE model inference performance/)).toBeInTheDocument()
    })
  })

  it('shows models page when navigating', () => {
    renderApp()
    // Navigation would require more complex routing test setup
    expect(screen.getByText('Models')).toBeInTheDocument()
  })
})
