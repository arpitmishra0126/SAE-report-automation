import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Loader2 } from 'lucide-react'
import { Layout } from '../components/Layout'
import { UploadDropzone } from '../components/UploadDropzone'
import { Button } from '../components/Button'
import { createReport, getErrorMessage } from '../services/reportService'
import type { PipelineStatus } from '../types'

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<PipelineStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const navigate = useNavigate()

  const isBusy = status === 'uploading' || status === 'processing'

  const handleFileSelected = (selected: File | null) => {
    setFile(selected)
    setStatus('idle')
    setErrorMessage(null)
  }

  const handleGenerate = async () => {
    if (!file) return

    setStatus('uploading')
    setErrorMessage(null)

    try {
      const result = await createReport(file, (percent) => {
        // The request body finishes uploading well before the
        // pipeline (OCR + LLM) finishes running on the server.
        if (percent >= 100) setStatus('processing')
      })

      setStatus('success')
      navigate('/results', {
        state: {
          fileName: file.name,
          caseSummary: result.caseSummary,
          docxUrl: result.docxUrl,
        },
      })
    } catch (error) {
      setStatus('error')
      setErrorMessage(getErrorMessage(error))
    }
  }

  return (
    <Layout>
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-slate-900">
          SAE Report Automation
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Automated SAE Case Summary Generation System
        </p>
      </div>

      <div className="mt-10">
        <UploadDropzone file={file} onFileSelected={handleFileSelected} />
      </div>

      {status === 'error' && errorMessage && (
        <div className="mt-6 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={1.75} />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="mt-8 flex justify-center">
        <Button onClick={handleGenerate} disabled={!file || isBusy}>
          {isBusy && <Loader2 className="h-4 w-4 animate-spin" strokeWidth={2} />}
          {status === 'uploading' && 'Uploading…'}
          {status === 'processing' && 'Processing…'}
          {!isBusy && 'Generate Report'}
        </Button>
      </div>
    </Layout>
  )
}
