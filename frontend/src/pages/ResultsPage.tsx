import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, FileJson, FileText, ArrowLeft } from 'lucide-react'
import { Layout } from '../components/Layout'
import { Button } from '../components/Button'
import { resolveDocxUrl } from '../services/reportService'
import type { CaseSummary } from '../types'

interface ResultsLocationState {
  fileName?: string
  caseSummary?: CaseSummary
  docxUrl?: string | null
}

function downloadJson(caseSummary: CaseSummary, fileName?: string) {
  const blob = new Blob([JSON.stringify(caseSummary, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${caseSummary.case_id ?? fileName ?? 'report'}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

export function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { fileName, caseSummary, docxUrl } =
    (location.state as ResultsLocationState) ?? {}

  return (
    <Layout>
      <div className="text-center">
        <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" strokeWidth={1.75} />
        <h1 className="mt-5 text-xl font-semibold text-slate-900">
          Report Ready
        </h1>
        {fileName && (
          <p className="mt-1 text-sm text-slate-500">{fileName}</p>
        )}
      </div>

      <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        <Button
          variant="secondary"
          disabled={!caseSummary}
          onClick={() => caseSummary && downloadJson(caseSummary, fileName)}
        >
          <FileJson className="h-4 w-4" strokeWidth={1.75} />
          Download JSON
        </Button>

        {docxUrl ? (
          <a
            href={resolveDocxUrl(docxUrl)}
            className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            <FileText className="h-4 w-4" strokeWidth={1.75} />
            Download DOCX
          </a>
        ) : (
          <Button variant="secondary" disabled>
            <FileText className="h-4 w-4" strokeWidth={1.75} />
            Download DOCX
          </Button>
        )}
      </div>

      {!caseSummary && (
        <p className="mt-6 text-center text-xs text-slate-400">
          No report data available. Generate a report from the upload page
          first.
        </p>
      )}

      <div className="mt-10 flex justify-center">
        <Button variant="secondary" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4" strokeWidth={1.75} />
          Process another report
        </Button>
      </div>
    </Layout>
  )
}
