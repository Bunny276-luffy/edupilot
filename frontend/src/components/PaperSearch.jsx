import { useState } from 'react'
import axios from 'axios'
import { Search, Loader2, BookOpen, FileText, AlertCircle } from 'lucide-react'

export default function PaperSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const res = await axios.post('/api/search/papers', {
        query: query.trim(),
        top_k: 5,
      })
      setResults(res.data.results || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter') search()
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="mb-6">
        <h2 className="font-display font-bold text-2xl text-white mb-1">Past Papers Search</h2>
        <p className="text-slate-400 text-sm">
          Search university question banks using Elasticsearch full-text search.
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKey}
            className="input pl-10"
            placeholder='e.g. "Binary Trees from DBMS", "OS scheduling algorithms"'
            id="search-papers-input"
          />
        </div>
        <button
          onClick={search}
          disabled={loading || !query.trim()}
          className="btn-primary flex items-center gap-2"
          id="btn-search-papers"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="card p-4 border-red-500/30 bg-red-500/10 mb-4">
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-5 shimmer h-24 rounded-2xl" />
          ))}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="card p-10 text-center">
          <BookOpen size={32} className="text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No results found</p>
          <p className="text-slate-600 text-sm mt-1">Try different keywords or a broader topic.</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-4 animate-fade-in">
          <p className="text-xs text-slate-500 font-medium">
            {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
          </p>
          {results.map((r, i) => (
            <div
              key={r.id}
              className="card p-5 hover:border-brand-orange/30 transition-colors duration-200"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-blue/30 flex items-center justify-center text-blue-400 text-xs font-bold shrink-0 mt-0.5">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  {/* Highlighted text */}
                  {r.highlight && r.highlight.length > 0 ? (
                    <p
                      className="text-slate-200 text-sm leading-relaxed mb-2"
                      dangerouslySetInnerHTML={{ __html: r.highlight[0] }}
                    />
                  ) : (
                    <p className="text-slate-200 text-sm leading-relaxed mb-2">
                      {r.question_text}
                    </p>
                  )}

                  {/* Metadata chips */}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {r.subject && (
                      <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full">
                        {r.subject}
                      </span>
                    )}
                    {r.topic && (
                      <span className="text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-full">
                        {r.topic}
                      </span>
                    )}
                    {r.year && (
                      <span className="text-xs bg-brand-orange/10 text-brand-amber border border-brand-orange/20 px-2 py-0.5 rounded-full">
                        {r.year}
                      </span>
                    )}
                  </div>

                  {/* Source */}
                  <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                    <FileText size={11} />
                    <span>{r.source_document}</span>
                    {r.page && <span>— Page {r.page}</span>}
                    {r.university && (
                      <>
                        <span className="text-slate-700">·</span>
                        <span>{r.university}</span>
                      </>
                    )}
                    <span className="text-slate-700">·</span>
                    <span className="text-brand-amber">Score: {r.score?.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tip */}
      {!searched && (
        <div className="card p-5 border-blue-500/20 bg-blue-500/5">
          <p className="text-sm text-slate-400 leading-relaxed">
            <span className="text-blue-400 font-semibold">Tip:</span> Try queries like{' '}
            <button
              onClick={() => { setQuery('Binary Trees from DBMS'); }}
              className="text-brand-amber underline hover:no-underline"
            >
              "Binary Trees from DBMS"
            </button>
            {' '}or{' '}
            <button
              onClick={() => { setQuery('quicksort algorithm analysis'); }}
              className="text-brand-amber underline hover:no-underline"
            >
              "quicksort algorithm analysis"
            </button>
          </p>
        </div>
      )}
    </div>
  )
}
