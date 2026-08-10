import axios from 'axios'

/**
 * Origin of the FastAPI bridge (`src/api.py`), e.g. no path suffix.
 * Configurable so it can be pointed elsewhere without touching code.
 */
export const API_ORIGIN = import.meta.env.VITE_API_ORIGIN ?? 'http://localhost:8000'

/** Shared Axios instance for all backend calls. */
export const apiClient = axios.create({
  baseURL: `${API_ORIGIN}/api`,
  timeout: 5 * 60 * 1000, // the pipeline (OCR + LLM) can take a while
})
