import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

interface Coll { id: string; name: string; description: string; document_count: number }
interface Doc { id: string; original_name: string }

export default function Collections() {
  const { t } = useI18n()
  const [colls, setColls] = useState<Coll[]>([])
  const [allDocs, setAllDocs] = useState<Doc[]>([])
  const [sel, setSel] = useState<string | null>(null)
  const [cDocs, setCDocs] = useState<Doc[]>([])
  const [name, setName] = useState(''); const [desc, setDesc] = useState('')

  const load = useCallback(() => { api.getCollections().then(d => setColls(d.collections || [])); api.getDocuments().then(d => setAllDocs(d.documents || [])) }, [])
  useEffect(() => { load() }, [load])
  useEffect(() => { if (sel) api.getCollection(sel).then(d => setCDocs(d.documents || [])); else setCDocs([]) }, [sel])

  const ids = new Set(cDocs.map(d => d.id))
  const avail = allDocs.filter(d => !ids.has(d.id))
  const inp = "w-full px-3 py-2 border border-slate-300 dark:border-zinc-600 rounded-lg text-sm bg-white dark:bg-zinc-900 text-slate-900 dark:text-slate-100"

  return (<div>
    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">{t('coll.title')}</h2>
    <div className="flex gap-6">
      <div className="w-72 space-y-3">
        <div className="bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl p-4 space-y-2">
          <input value={name} onChange={e => setName(e.target.value)} placeholder={t('coll.name')} className={inp} />
          <input value={desc} onChange={e => setDesc(e.target.value)} placeholder={t('coll.desc')} className={inp} />
          <button onClick={async () => { if (!name.trim()) return; await api.createCollection(name, desc); setName(''); setDesc(''); load() }}
            className="w-full px-3 py-2 bg-slate-900 dark:bg-indigo-600 text-white rounded-lg text-sm hover:bg-slate-700 dark:hover:bg-indigo-500 font-medium transition-colors">{t('coll.create')}</button>
        </div>
        {colls.map(c => (
          <div key={c.id} onClick={() => setSel(c.id)}
            className={`bg-white dark:bg-zinc-800 border rounded-xl p-4 cursor-pointer transition-all ${sel === c.id ? 'border-indigo-500 ring-1 ring-indigo-500/20' : 'border-slate-200 dark:border-zinc-700 hover:border-slate-300'}`}>
            <div className="flex justify-between"><div><p className="font-semibold text-sm text-slate-900 dark:text-slate-100">{c.name}</p>
              {c.description && <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">{c.description}</p>}</div>
              <button onClick={e => { e.stopPropagation(); if (confirm(t('coll.confirm'))) { api.deleteCollection(c.id); if (sel === c.id) setSel(null); load() } }} className="text-xs text-red-400 hover:text-red-500">x</button>
            </div><p className="text-xs text-slate-400 dark:text-zinc-500 mt-2 tabular-nums">{c.document_count}{t('coll.docs')}</p>
          </div>))}
        {colls.length === 0 && <p className="text-sm text-slate-400 dark:text-zinc-500 text-center py-6">{t('coll.empty')}</p>}
      </div>
      <div className="flex-1">{sel ? (<div className="space-y-6">
        <div><h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">{t('coll.in')}</h3>
          {cDocs.length === 0 ? <p className="text-sm text-slate-400 dark:text-zinc-500 py-4">{t('coll.no_docs')}</p> :
            <div className="space-y-1">{cDocs.map(d => (<div key={d.id} className="flex items-center justify-between bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg px-4 py-2.5 text-sm">
              <span className="text-slate-700 dark:text-slate-200">{d.original_name}</span>
              <button onClick={async () => { await api.removeDocsFromCollection(sel, [d.id]); api.getCollection(sel).then(d2 => setCDocs(d2.documents || [])); load() }} className="text-xs text-red-500 font-medium">{t('coll.remove')}</button>
            </div>))}</div>}</div>
        <div><h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">{t('coll.available')}</h3>
          {avail.length === 0 ? <p className="text-sm text-slate-400 dark:text-zinc-500">{t('coll.all_in')}</p> :
            <div className="space-y-1">{avail.map(d => (<div key={d.id} className="flex items-center justify-between bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-lg px-4 py-2.5 text-sm hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors">
              <span className="text-slate-500 dark:text-zinc-400">{d.original_name}</span>
              <button onClick={async () => { await api.addDocsToCollection(sel, [d.id]); api.getCollection(sel).then(d2 => setCDocs(d2.documents || [])); load() }} className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">+ {t('coll.add')}</button>
            </div>))}</div>}</div>
      </div>) : <div className="text-center py-20 text-slate-400 dark:text-zinc-500">{t('coll.select')}</div>}</div>
    </div>
  </div>)
}
