import { useState, useEffect } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

interface Result { chunk_id: string; content: string; score: number; match_type: string; file_name: string }
interface Coll { id: string; name: string; document_count: number }

export default function Search() {
  const { t } = useI18n()
  const [q, setQ] = useState(''); const [mode, setMode] = useState('hybrid'); const [topK, setTopK] = useState(10)
  const [collId, setCollId] = useState(''); const [colls, setColls] = useState<Coll[]>([])
  const [results, setResults] = useState<Result[]>([]); const [loading, setLoading] = useState(false); const [ms, setMs] = useState(0)
  useEffect(() => { api.getCollections().then(d => setColls(d.collections || [])).catch(() => {}) }, [])

  const search = async () => { if (!q.trim()) return; setLoading(true); const t0 = Date.now(); try { const d = await api.search(q, mode, topK, collId || undefined); setResults(d.results || []); setMs(Date.now() - t0) } finally { setLoading(false) } }
  const sel = "px-3 py-2.5 border border-slate-300 dark:border-zinc-600 rounded-lg text-sm bg-white dark:bg-zinc-800 text-slate-700 dark:text-slate-200"

  return (<div>
    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">{t('search.title')}</h2>
    <div className="flex gap-3 mb-6 flex-wrap">
      <input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} placeholder={t('search.placeholder')}
        className="flex-1 min-w-[200px] px-4 py-2.5 border border-slate-300 dark:border-zinc-600 rounded-lg text-sm bg-white dark:bg-zinc-800 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all" />
      <select value={mode} onChange={e => setMode(e.target.value)} className={sel}><option value="hybrid">Hybrid</option><option value="vector">Vector</option><option value="fts">FTS</option><option value="graph">Graph</option></select>
      <select value={collId} onChange={e => setCollId(e.target.value)} className={sel}><option value="">{t('search.all')}</option>{colls.map(c => <option key={c.id} value={c.id}>{c.name} ({c.document_count})</option>)}</select>
      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400"><span>Top-K: {topK}</span><input type="range" min={1} max={20} value={topK} onChange={e => setTopK(+e.target.value)} className="accent-indigo-500" /></div>
      <button onClick={search} disabled={loading} className="px-5 py-2.5 bg-slate-900 dark:bg-indigo-600 text-white rounded-lg text-sm hover:bg-slate-700 dark:hover:bg-indigo-500 disabled:opacity-50 font-medium transition-colors">{loading ? t('search.searching') : t('search.button')}</button>
    </div>
    {results.length > 0 && <p className="text-xs text-slate-400 dark:text-zinc-500 mb-4 tabular-nums">{results.length}{t('search.results')}{ms}ms</p>}
    <div className="space-y-3">{results.map((r, i) => (
      <div key={r.chunk_id || i} className="bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl p-5 hover:shadow-md dark:hover:border-zinc-600 transition-all">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[11px] font-mono bg-slate-100 dark:bg-zinc-700 text-slate-600 dark:text-zinc-300 px-2 py-0.5 rounded">{r.match_type}</span>
          <span className="text-xs text-slate-400 dark:text-zinc-500">{r.file_name?.split('/').pop()}</span><div className="flex-1" />
          <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 tabular-nums">{(r.score * 100).toFixed(1)}%</span>
        </div><p className="text-sm text-slate-700 dark:text-zinc-300 leading-relaxed line-clamp-3">{r.content}</p>
      </div>))}
      {results.length === 0 && !loading && q && <div className="text-center py-12 text-slate-400 dark:text-zinc-500">{t('search.no_results')}</div>}
    </div>
  </div>)
}
