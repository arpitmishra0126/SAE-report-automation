import { useCallback, useRef, useState } from 'react'
import type { DragEvent } from 'react'
import { UploadCloud, FileText, X } from 'lucide-react'

interface UploadDropzoneProps {
  file: File | null
  onFileSelected: (file: File | null) => void
}

function isPdf(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function UploadDropzone({ file, onFileSelected }: UploadDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      const selected = fileList?.[0]

      if (!selected) return

      if (!isPdf(selected)) {
        setError('Only PDF files are accepted.')
        return
      }

      setError(null)
      onFileSelected(selected)
    },
    [onFileSelected],
  )

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragActive(false)
    handleFiles(event.dataTransfer.files)
  }

  const handleRemove = () => {
    onFileSelected(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click()
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragActive(true)
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-16 text-center transition-colors cursor-pointer ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-slate-300 bg-white hover:border-slate-400'
        }`}
      >
        <UploadCloud
          className="mb-4 h-9 w-9 text-slate-400"
          strokeWidth={1.5}
        />
        <p className="text-sm font-medium text-slate-700">Drop PDF here</p>
        <p className="my-1 text-xs text-slate-400">or</p>
        <span className="mt-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Browse files
        </span>

        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {file && (
        <div className="mt-4 flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <FileText className="h-5 w-5 shrink-0 text-blue-700" strokeWidth={1.75} />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-700">
                {file.name}
              </p>
              <p className="text-xs text-slate-400">{formatFileSize(file.size)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            aria-label="Remove selected file"
            className="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
