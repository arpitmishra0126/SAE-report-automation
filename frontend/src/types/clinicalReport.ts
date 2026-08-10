/**
 * TypeScript mirror of `src/reasoning/report.py :: ClinicalReport`,
 * the AI-generated narrative report produced from a CaseSummary.
 *
 * The backend's row entries (clinical_timeline, daily_clinical_
 * monitoring, neonatal_sepsis, laboratory_findings) are emitted by
 * the LLM as loosely-typed JSON objects rather than a fixed schema,
 * so they're kept as `Record<string, unknown>` here rather than
 * invented as strict interfaces.
 */

export type ReportRow = Record<string, unknown>

export interface ClinicalReport {
  executive_summary: string
  maternal_history: string

  clinical_timeline: ReportRow[]
  daily_clinical_monitoring: ReportRow[]
  neonatal_sepsis: ReportRow[]
  laboratory_findings: ReportRow[]

  final_outcome: string
  quality_flags: string[]

  metadata: Record<string, unknown>
}
