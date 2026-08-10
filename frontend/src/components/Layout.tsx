import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Stethoscope } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center gap-2 px-6 py-4">
          <Link to="/" className="flex items-center gap-2 text-slate-700">
            <Stethoscope className="h-5 w-5 text-blue-700" strokeWidth={1.75} />
            <span className="text-sm font-medium tracking-tight">
              SAE Report Automation
            </span>
          </Link>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-2xl">{children}</div>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        For research and clinical documentation use.
      </footer>
    </div>
  )
}
