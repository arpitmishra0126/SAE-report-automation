/**
 * Backend endpoint paths for the FastAPI bridge (`src/api.py`).
 *
 * Paths here are relative to `apiClient`'s baseURL (`${API_ORIGIN}/api`).
 */

export const ENDPOINTS = {
  /** POST a PDF file; runs the existing SAEPipeline synchronously. */
  createReport: '/reports',
} as const
