import axios from 'axios'
import { apiClient, API_ORIGIN } from './apiClient'
import { ENDPOINTS } from './endpoints'
import type { CaseSummary } from '../types'

/** Matches the response shape of POST /api/reports in src/api.py. */
export interface CreateReportResponse {
  caseSummary: CaseSummary
  docxUrl: string | null
}

export async function createReport(
  file: File,
  onUploadProgress?: (percent: number) => void,
): Promise<CreateReportResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await apiClient.post<CreateReportResponse>(
    ENDPOINTS.createReport,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (!onUploadProgress || !event.total) return
        onUploadProgress(Math.round((event.loaded / event.total) * 100))
      },
    },
  )

  return data
}

/** Turns the relative `docxUrl` returned by the API into a fetchable URL. */
export function resolveDocxUrl(docxUrl: string): string {
  return `${API_ORIGIN}${docxUrl}`
}

/** Extracts a human-readable message from a failed API call. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.code === 'ECONNABORTED') {
      return 'The request timed out. The report may still be processing.'
    }
    if (!error.response) {
      return 'Could not reach the server. Is the API running?'
    }
  }
  return 'Something went wrong while generating the report.'
}
