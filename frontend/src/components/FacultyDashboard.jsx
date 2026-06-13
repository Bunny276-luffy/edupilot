import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { Upload, FileText, AlertTriangle, Lightbulb, Loader2, CheckCircle2 } from 'lucide-react'
import BloomAnalysis, { classifyWithBackend, classifyWithGemini } from './BloomAnalysis'

const bloomColors = {
  Remember: 'bloom-remember',
  Understand: 'bloom-understand',
  Apply: 'bloom-apply',
  Analyze: 'bloom-analyze',
  Evaluate: 'bloom-evaluate',
  Create: 'bloom-create',
}

export default function FacultyDashboard({ courseId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [textInput, setTextInput] = useState('')
  const [uploadMode, setUploadMode] = useState('file') // 'file' | 'text'

  const handleSubmit = async (file) => {
    setLoading(true)
    setError(null)
    setResult(null)

    // ── Backend first, Gemini direct as fallback ────────────────────────────────
    // For file uploads we still use multipart (backend only); for text we try
    // both paths with automatic fallback.
    try {
      if (file) {
        // File path: always multipart POST to backend
        const formData = new FormData()
        formData.append('course_id', courseId || 'CS301')
        formData.append('uploaded_by', 'faculty')
        formData.append('file', file)
        const res = await axios.post('/api/faculty/upload-questions', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        console.log('[Bloom] backend')
        setResult(res.data)
      } else {
        // Text path: try backend JSON first, then Gemini direct
        let normalized = null
        try {
          const raw = await classifyWithBackend({
            course_id: courseId || 'CS301',
            questions_text: textInput,
          })
          console.log('[Bloom] backend')
          // Normalize backend shape → same shape the UI already expects
          normalized = {
            classified: raw.classified,
            total: raw.total ?? raw.classified?.length ?? 0,
            warning: raw.warning,
            suggestions: raw.suggestions,
          }
        } catch (backendErr) {
          console.log('[Bloom] gemini-direct')
          const questions = textInput
            .split('\n')
            .map((q) => q.replace(/^\d+[.)\s]+/, '').trim())
            .filter(Boolean)
          const raw = await classifyWithGemini(questions)
          // Normalize Gemini shape → same shape the UI already expects
          normalized = {
            classified: raw.map((item) => ({
              question_text: item.question,
              blooms_level: item.level,
              reasoning: item.reasoning,
              co_mapping: [],
            })),
            total: raw.length,
            warning: null,
            suggestions: [],
          }
        }
        setResult(normalized)
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to analyse questions. Is the backend running?'
      )
    } finally {
      setLoading(false)
    }
  }

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) handleSubmit(accepted[0])
  }, [courseId])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] },
    maxFiles: 1,
  })

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="font-display font-bold text-2xl text-white mb-1">Upload Question Paper</h2>
        <p className="text-slate-400 text-sm">Upload a PDF or paste questions to analyse Bloom's taxonomy distribution.</p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-5">
        {['file', 'text'].map((m) => (
          <button
            key={m}
            onClick={() => setUploadMode(m)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all duration-200 ${
              uploadMode === m
                ? 'bg-brand-blue text-white'
                : 'text-slate-400 hover:text-white bg-white/5'
            }`}
          >
            {m === 'file' ? '📄 Upload PDF' : '✏️ Paste Text'}
          </button>
        ))}
      </div>

      {/* Upload zone */}
      {uploadMode === 'file' ? (
        <div
          {...getRootProps()}
          id="dropzone"
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragActive
              ? 'border-brand-orange bg-brand-orange/10 scale-[1.01]'
              : 'border-brand-border hover:border-brand-orange/50 hover:bg-white/5'
          }`}
        >
          <input {...getInputProps()} />
          <Upload size={36} className="mx-auto mb-4 text-slate-500" />
          <p className="text-white font-semibold mb-1">
            {isDragActive ? 'Drop the file here...' : 'Drag & drop a question paper'}
          </p>
          <p className="text-slate-500 text-sm">Supports PDF and TXT — up to 10 MB</p>
        </div>
      ) : (
        <div className="card p-5">
          <label className="label">Paste exam questions (one per line)</label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={8}
            className="input resize-none mb-4 font-mono text-sm"
            placeholder="1. What is a binary tree?&#10;2. Explain the working of quicksort.&#10;3. Design a hash function that minimises collisions."
          />
          <button
            onClick={() => handleSubmit(null)}
            disabled={loading || !textInput.trim()}
            className="btn-primary w-full flex items-center justify-center gap-2"
            id="btn-analyse-text"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
            {loading ? 'Analysing with Gemini...' : 'Analyse Questions'}
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="mt-8 card p-8 text-center">
          <Loader2 size={36} className="animate-spin text-brand-orange mx-auto mb-4" />
          <p className="text-white font-semibold mb-1">Classifying with Gemini 1.5 Pro...</p>
          <p className="text-slate-400 text-sm">Each question is analysed individually for accuracy.</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 card p-4 border-red-500/30 bg-red-500/10">
          <div className="flex items-center gap-3 text-red-400">
            <AlertTriangle size={18} />
            <span className="text-sm font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="mt-8 space-y-6 animate-fade-in">
          {/* Bloom Analysis */}
          <BloomAnalysis
            distribution={result.classified
              .reduce((acc, q) => {
                const lvl = q.blooms_level
                const existing = acc.find((x) => x.level === lvl)
                if (existing) existing.count++
                else acc.push({ level: lvl, count: 1, percentage: 0 })
                return acc
              }, [])
              .map((item) => ({
                ...item,
                percentage: Math.round((item.count / result.total) * 100),
              }))}
            total={result.total}
          />

          {/* Warning */}
          {result.warning && (
            <div className="card p-4 border-yellow-500/30 bg-yellow-500/10">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-yellow-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-yellow-300 font-semibold text-sm mb-1">NBA Compliance Warning</p>
                  <p className="text-yellow-400/80 text-sm">{result.warning}</p>
                </div>
              </div>
            </div>
          )}

          {/* Suggestions */}
          {result.suggestions && result.suggestions.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb size={18} className="text-brand-amber" />
                <h3 className="font-semibold text-white">AI-Suggested Higher-Order Questions</h3>
              </div>
              <div className="space-y-3">
                {result.suggestions.map((s, i) => (
                  <div
                    key={i}
                    className="p-3 bg-brand-orange/10 border border-brand-orange/20 rounded-xl text-sm text-slate-300"
                  >
                    <span className="text-brand-amber font-semibold mr-2">Q{i + 1}.</span>
                    {s}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Question List */}
          <div className="card p-5">
            <h3 className="font-semibold text-white mb-4">
              Classified Questions ({result.total})
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {result.classified.map((q, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 bg-brand-surface rounded-xl border border-brand-border"
                >
                  <span
                    className={`badge shrink-0 mt-0.5 border ${bloomColors[q.blooms_level] || 'bloom-understand'}`}
                  >
                    {q.blooms_level}
                  </span>
                  <div className="min-w-0">
                    <p className="text-slate-200 text-sm">{q.question_text}</p>
                    <p className="text-slate-500 text-xs mt-1 italic">{q.reasoning}</p>
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {q.co_mapping.map((co) => (
                        <span key={co} className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">
                          {co}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
