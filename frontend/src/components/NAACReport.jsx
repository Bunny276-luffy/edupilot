import { useState } from 'react'
import axios from 'axios'
import { FileText, Download, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react'

export default function NAACReport({ courseId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [semester, setSemester] = useState('Even 2024-25')
  const [year, setYear] = useState('2024-25')

  const generate = async () => {
    setLoading(true)
    setError(null)
    setSuccess(false)
    try {
      const res = await axios.get(
        `/api/faculty/naac-report/${courseId}?semester=${semester}&academic_year=${year}`,
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `NAAC_Report_${courseId}_${year}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
      setSuccess(true)
    } catch (err) {
      const text = await err.response?.data?.text?.()
      let detail = 'Failed to generate NAAC report.'
      try {
        const parsed = JSON.parse(text)
        detail = parsed.detail || detail
      } catch {}
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h2 className="font-display font-bold text-2xl text-white mb-1">NAAC Report Generator</h2>
        <p className="text-slate-400 text-sm">
          One-click generation of a complete NAAC/NBA-compliant accreditation PDF report.
        </p>
      </div>

      {/* Report info card */}
      <div className="card p-6 mb-6">
        <h3 className="font-semibold text-white mb-4">Report Contents</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            "Executive summary (AI-generated)",
            "Bloom's taxonomy distribution table",
            "CO attainment levels with NBA scale",
            "CO-PO program outcome summary",
            "Course and faculty details",
            "College-branded header & footer",
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2.5 text-sm text-slate-300">
              <CheckCircle2 size={14} className="text-green-400 shrink-0" />
              {item}
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="card p-5 mb-6">
        <h3 className="font-semibold text-white mb-4">Report Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Course ID</label>
            <input value={courseId} readOnly className="input bg-brand-surface cursor-not-allowed" />
          </div>
          <div>
            <label className="label">Semester</label>
            <input
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="label">Academic Year</label>
            <input value={year} onChange={(e) => setYear(e.target.value)} className="input" />
          </div>
        </div>
      </div>

      {error && (
        <div className="card p-4 border-red-500/30 bg-red-500/10 mb-6">
          <div className="flex items-center gap-3 text-red-400">
            <AlertTriangle size={18} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        </div>
      )}

      {success && (
        <div className="card p-4 border-green-500/30 bg-green-500/10 mb-6">
          <div className="flex items-center gap-3 text-green-400">
            <CheckCircle2 size={18} />
            <span className="text-sm font-medium">
              NAAC Report downloaded successfully!
            </span>
          </div>
        </div>
      )}

      {/* Generate button */}
      <button
        onClick={generate}
        disabled={loading}
        id="btn-generate-naac"
        className="btn-primary w-full flex items-center justify-center gap-3 py-4 text-base"
      >
        {loading ? (
          <>
            <Loader2 size={20} className="animate-spin" />
            Generating AI Summary & PDF...
          </>
        ) : (
          <>
            <FileText size={20} />
            Generate & Download NAAC Report
          </>
        )}
      </button>

      {loading && (
        <div className="mt-4 text-center text-slate-400 text-sm">
          Gemini AI is writing your executive summary. This may take 10–15 seconds...
        </div>
      )}

      {/* Compliance note */}
      <div className="mt-8 card p-4 border-blue-500/20 bg-blue-500/5">
        <p className="text-xs text-blue-400 leading-relaxed">
          <strong>Compliance note:</strong> This report conforms to NBA Criterion 2.3 (Assessment of
          Course Outcomes) and NAAC Criterion 1.2 (Academic Flexibility). Always have a human expert
          review before submission.
        </p>
      </div>
    </div>
  )
}
