import { useLocation } from 'react-router-dom'
import { Loader2, FileSearch, Cpu, FileCheck } from 'lucide-react'
import { Layout } from '../components/Layout'

interface ProcessingLocationState {
  fileName?: string
}

const steps = [
  { icon: FileSearch, label: 'Reading PDF' },
  { icon: Cpu, label: 'Extracting clinical data' },
  { icon: FileCheck, label: 'Generating report' },
]

export function ProcessingPage() {
  const location = useLocation()
  const { fileName } = (location.state as ProcessingLocationState) ?? {}

  return (
    <Layout>
      <div className="text-center">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-700" strokeWidth={1.75} />
        <h1 className="mt-5 text-xl font-semibold text-slate-900">
          Processing your report
        </h1>
        {fileName && (
          <p className="mt-1 text-sm text-slate-500">{fileName}</p>
        )}
      </div>

      <ul className="mx-auto mt-10 max-w-xs space-y-4">
        {steps.map(({ icon: Icon, label }) => (
          <li
            key={label}
            className="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-3"
          >
            <Icon className="h-4 w-4 text-slate-400" strokeWidth={1.75} />
            <span className="text-sm text-slate-600">{label}</span>
          </li>
        ))}
      </ul>

      <p className="mt-10 text-center text-xs text-slate-400">
        This step will connect to the extraction pipeline once the backend
        API is available.
      </p>
    </Layout>
  )
}
