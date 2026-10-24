import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
    }),
  },
}))
