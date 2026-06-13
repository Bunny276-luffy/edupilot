import { useState, useEffect } from 'react'
import axios from 'axios'
import { Zap, RefreshCw, AlertCircle, Loader2 } from 'lucide-react'

const statusColor = (err) => (err ? 'text-red-400' : 'text-green-400')

function TraceRow({ trace }) {
  const latencyColor =
    trace.latency_ms > 3000
      ? 'text-red-400'
      : trace.latency_ms > 1500
      ? 'text-yellow-400'
      : 'text-green-400'

  return (
    <tr className="border-t border-brand-border hover:bg-white/5 transition-colors">
      <td className="px-4 py-3 text-xs text-slate-500 font-mono whitespace-nowrap">
        {new Date(trace.timestamp).toLocaleTimeString()}
      </td>
      <td className="px-4 py-3">
        <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
          {trace.tag}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-slate-400 font-mono max-w-[200px] truncate" title={trace.prompt}>
        {trace.prompt}
      </td>
      <td className="px-4 py-3 text-xs text-slate-300 max-w-[200px] truncate" title={trace.response}>
        {trace.response}
      </td>
      <td className={`px-4 py-3 text-xs font-mono font-semibold ${latencyColor}`}>
        {trace.latency_ms?.toFixed(0)}ms
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">{trace.token_count}</td>
      <td className={`px-4 py-3 text-xs font-semibold ${statusColor(trace.error)}`}>
        {trace.error ? '✗ Error' : '✓ OK'}
      </td>
    </tr>
  )
}

export default function AdminTraces() {
  const [traces, setTraces] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchTraces = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get('/api/admin/traces?limit=20')
      setTraces(res.data.traces || [])
    } catch (err) {
      setError('Failed to fetch traces.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTraces()
  }, [])

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-display font-bold text-2xl text-white mb-1">AI Trace Logs</h2>
          <p className="text-slate-400 text-sm">
            Every Gemini call is traced via Arize Phoenix. Last 20 traces shown.
          </p>
        </div>
        <button
          onClick={fetchTraces}
          disabled={loading}
          className="btn-ghost flex items-center gap-2"
          id="btn-refresh-traces"
        >
          {loading ? (
            <Loader2 size={15} className="animate-spin" />
          ) : (
            <RefreshCw size={15} />
          )}
          Refresh
        </button>
      </div>

      {error && (
        <div className="card p-4 border-red-500/30 bg-red-500/10 mb-4">
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 size={28} className="animate-spin text-brand-orange mx-auto mb-3" />
            <p className="text-slate-400">Fetching traces...</p>
          </div>
        ) : traces.length === 0 ? (
          <div className="p-12 text-center">
            <Zap size={28} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No traces yet</p>
            <p className="text-slate-600 text-sm mt-1">
              Make some API calls first (upload questions or chat with the tutor).
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-brand-surface border-b border-brand-border">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Tag
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Prompt
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Response
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Latency
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {traces.map((t) => (
                  <TraceRow key={t.id} trace={t} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="mt-4 text-xs text-slate-600 text-center">
        Traces are stored in-memory. Configure{' '}
        <code className="text-slate-500">ARIZE_API_KEY</code> and{' '}
        <code className="text-slate-500">ARIZE_SPACE_KEY</code> to push to Arize cloud dashboard.
      </div>
    </div>
  )
}
