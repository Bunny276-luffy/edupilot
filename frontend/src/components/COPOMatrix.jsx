import { useState } from 'react'
import axios from 'axios'
import { Loader2, Download, AlertTriangle, BarChart3, RefreshCw } from 'lucide-react'

const attainmentColor = (val) => {
  if (val >= 2.5) return 'text-green-400 bg-green-500/15 border-green-500/30'
  if (val >= 1.5) return 'text-yellow-400 bg-yellow-500/15 border-yellow-500/30'
  if (val > 0) return 'text-red-400 bg-red-500/15 border-red-500/30'
  return 'text-slate-600 bg-transparent border-transparent'
}

export default function COPOMatrix({ courseId }) {
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState(null)
  const [matrix, setMatrix] = useState(null)
  const [semester, setSemester] = useState('Even 2024-25')
  const [year, setYear] = useState('2024-25')

  const generate = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post('/api/faculty/generate-copo', {
        course_id: courseId,
        semester,
        academic_year: year,
      })
      setMatrix(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate matrix.')
    } finally {
      setLoading(false)
    }
  }

  const downloadPDF = async () => {
    setDownloading(true)
    try {
      const res = await axios.get(
        `/api/faculty/copo-pdf/${courseId}?semester=${semester}&academic_year=${year}`,
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `COPO_${courseId}_${year}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('PDF download failed.')
    } finally {
      setDownloading(false)
    }
  }

  const cos = matrix ? matrix.cos : []
  const pos = matrix ? matrix.pos : []
  const cellMap = {}
  if (matrix) {
    matrix.cells.forEach((c) => {
      cellMap[`${c.co_id}|${c.po_id}`] = c.attainment
    })
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="font-display font-bold text-2xl text-white mb-1">CO-PO Attainment Matrix</h2>
        <p className="text-slate-400 text-sm">
          Auto-generated from classified questions stored in MongoDB.
        </p>
      </div>

      {/* Controls */}
      <div className="card p-5 mb-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-36">
            <label className="label">Semester</label>
            <input
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              className="input"
              placeholder="Even 2024-25"
            />
          </div>
          <div className="flex-1 min-w-36">
            <label className="label">Academic Year</label>
            <input
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="input"
              placeholder="2024-25"
            />
          </div>
          <button
            onClick={generate}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 h-[42px]"
            id="btn-generate-copo"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <RefreshCw size={16} />
            )}
            {loading ? 'Generating...' : 'Generate Matrix'}
          </button>
          {matrix && (
            <button
              onClick={downloadPDF}
              disabled={downloading}
              className="btn-primary flex items-center gap-2 h-[42px]"
              id="btn-download-copo"
            >
              {downloading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Download size={16} />
              )}
              {downloading ? 'Exporting...' : 'Export PDF'}
            </button>
          )}
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

      {loading && (
        <div className="card p-12 text-center">
          <Loader2 size={36} className="animate-spin text-brand-orange mx-auto mb-4" />
          <p className="text-white font-semibold">Calculating attainment scores...</p>
        </div>
      )}

      {matrix && !loading && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card p-4 text-center">
              <div className="font-black text-3xl text-brand-amber">{matrix.avg_attainment?.toFixed(2)}</div>
              <div className="text-slate-400 text-sm mt-1">Avg CO Attainment / 3.00</div>
            </div>
            <div className="card p-4 text-center">
              <div className="font-black text-3xl text-blue-400">{matrix.total_questions}</div>
              <div className="text-slate-400 text-sm mt-1">Questions Analysed</div>
            </div>
            <div className="card p-4 text-center">
              <div className="font-black text-3xl text-green-400">{cos.length}</div>
              <div className="text-slate-400 text-sm mt-1">Course Outcomes</div>
            </div>
          </div>

          {/* Matrix table */}
          <div className="card p-5 overflow-x-auto">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 size={18} className="text-brand-orange" />
              <h3 className="font-semibold text-white">
                {matrix.course_name} ({matrix.course_code}) — {matrix.semester}
              </h3>
            </div>

            <table className="w-full text-sm border-separate border-spacing-1">
              <thead>
                <tr>
                  <th className="px-3 py-2 text-left text-slate-400 font-semibold bg-brand-surface rounded-lg">
                    CO \ PO
                  </th>
                  {pos.map((po) => (
                    <th
                      key={po}
                      className="px-3 py-2 text-center font-semibold text-white bg-brand-blue/40 rounded-lg min-w-[60px]"
                    >
                      {po}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-center font-semibold text-brand-amber bg-brand-orange/20 rounded-lg">
                    Attainment
                  </th>
                </tr>
              </thead>
              <tbody>
                {cos.map((co) => (
                  <tr key={co}>
                    <td className="px-3 py-2 font-semibold text-white bg-brand-surface rounded-lg">
                      {co}
                    </td>
                    {pos.map((po) => {
                      const val = cellMap[`${co}|${po}`] || 0
                      return (
                        <td key={po} className="px-3 py-2 text-center">
                          {val > 0 ? (
                            <span
                              className={`inline-block px-2 py-1 rounded-lg border text-xs font-bold ${attainmentColor(val)}`}
                            >
                              {val.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-slate-700">—</span>
                          )}
                        </td>
                      )
                    })}
                    <td className="px-3 py-2 text-center">
                      <span
                        className={`inline-block px-2 py-1 rounded-lg border text-xs font-bold ${attainmentColor(
                          matrix.co_attainment?.[co] || 0
                        )}`}
                      >
                        {(matrix.co_attainment?.[co] || 0).toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-green-500/30 border border-green-500/50 inline-block" />
                High (≥2.5)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-yellow-500/30 border border-yellow-500/50 inline-block" />
                Moderate (1.5–2.5)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-red-500/30 border border-red-500/50 inline-block" />
                Low (&lt;1.5)
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
