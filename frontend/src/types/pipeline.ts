/**
 * Frontend-only UI state types (not derived from the backend).
 */

export type PipelineStatus =
  | 'idle'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error'
