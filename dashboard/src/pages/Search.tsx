import { useState } from 'react'
import { api } from '../api'

interface Result { chunk_id: string; content: string; score: number; match_type: string; file_name: string }

export default function Search() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [topK, setTopK] = useState(10)
  const [results, setResults] = useState<Result[]>([])
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState(0)

  const onSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    const t0 = Date.now()
    try {
      const data = await api.search(query, mode, topK)
      setResults(data.results || [])
      setElapsed(Date.now() - t0)
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Search</h2>
      <div className="flex gap-3 mb-4">
        <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && onSearch()}
          placeholder="Enter search query..." className="flex-1 px-3 py-2 border rounded-md text-sm" />
        <select value={mode} onChange={e => setMode(e.target.value)} className="px-3 py-2 border rounded-md text-sm">
          <option value="hybrid">Hybrid</option><option value="vector">Vector</option>
          <option value="fts">FTS</option><option value="graph">Graph</option>
        </select>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>Top-K: {topK}</span>
          <input type="range" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} />
        </div>
        <button onClick={onSearch} disabled={loading} className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm hover:bg-gray-700 disabled:opacity-50">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      {results.length > 0 && <p className="text-xs text-gray-400 mb-4">{results.length} results in {elapsed}ms</p>}
      <div className="space-y-3">
        {results.map((r, i) => (
          <div key={r.chunk_id || i} className="border rounded-md p-4 hover:shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{r.match_type}</span>
              <span className="text-xs text-gray-400">{r.file_name}</span>
              <div className="flex-1" />
              <span className="text-xs font-medium">{(r.score * 100).toFixed(1)}%</span>
            </div>
            <p className="text-sm text-gray-700 line-clamp-3">{r.content}</p>
          </div>
        ))}
        {results.length === 0 && !loading && query && <div className="text-center py-8 text-gray-400">No results found.</div>}
      </div>
    </div>
  )
}
