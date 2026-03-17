import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

interface Doc { id: string; original_name: string; mime_type: string; status: string; chunk_count: number; created_at: string }
const badge: Record<string, string> = {
  uploaded: 'bg-slate-200 text-slate-700 dark:bg-zinc-700 dark:text-zinc-300',
  processing: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  vectorizing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  vectorized: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
}

export default function Documents() {
  const { t } = useI18n()
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)
  const load = useCallback(() => { api.getDocuments().then(d => setDocs(d.documents || [])).catch(() => {}) }, [])
  useEffect(() => { load(); const i = setInterval(load, 5000); return () => clearInterval(i) }, [load])
  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (!f) return; setUploading(true); try { await api.uploadDocument(f); load() } finally { setUploading(false); e.target.value = '' } }
  const onDelete = async (id: string) => { if (!confirm(t('docs.confirm'))) return; await api.deleteDocument(id); load() }

  return (<div>
    <div className="flex items-center justify-between mb-8">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t('docs.title')}</h2>
      <label className="px-4 py-2 bg-slate-900 dark:bg-indigo-600 text-white rounded-lg text-sm cursor-pointer hover:bg-slate-700 dark:hover:bg-indigo-500 transition-colors font-medium">
        {uploading ? t('docs.uploading') : t('docs.upload')}<input type="file" className="hidden" onChange={onUpload} disabled={uploading} />
      </label>
    </div>
    {docs.length === 0 ? <div className="text-center py-20 text-slate-400 dark:text-zinc-500">{t('docs.empty')}</div> : (
      <div className="bg-white dark:bg-zinc-800 rounded-xl border border-slate-200 dark:border-zinc-700 overflow-hidden">
        <table className="w-full text-sm"><thead><tr className="text-left text-slate-500 dark:text-zinc-400 border-b border-slate-200 dark:border-zinc-700 text-xs uppercase tracking-wider">
          <th className="px-4 py-3">{t('docs.name')}</th><th className="px-4 py-3">{t('docs.type')}</th><th className="px-4 py-3">{t('docs.status')}</th><th className="px-4 py-3">{t('docs.chunks')}</th><th className="px-4 py-3">{t('docs.date')}</th><th className="px-4 py-3"></th>
        </tr></thead><tbody>{docs.map(d => (
          <tr key={d.id} className="border-b border-slate-100 dark:border-zinc-700/50 hover:bg-slate-50 dark:hover:bg-zinc-700/30 transition-colors">
            <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-200">{d.original_name}</td>
            <td className="px-4 py-3 text-slate-500 dark:text-zinc-400">{d.mime_type?.split('/').pop()}</td>
            <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${badge[d.status] || ''}`}>{d.status}</span></td>
            <td className="px-4 py-3 text-slate-500 dark:text-zinc-400 tabular-nums">{d.chunk_count}</td>
            <td className="px-4 py-3 text-slate-400 dark:text-zinc-500 tabular-nums">{new Date(d.created_at).toLocaleDateString()}</td>
            <td className="px-4 py-3"><button onClick={() => onDelete(d.id)} className="text-red-500 hover:text-red-400 text-xs font-medium">{t('docs.delete')}</button></td>
          </tr>))}</tbody></table>
      </div>)}
  </div>)
}
