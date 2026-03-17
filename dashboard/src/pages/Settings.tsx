import { useState, useEffect } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

export default function Settings() {
  const { t } = useI18n()
  const [s, setS] = useState<Record<string, any>>({}); const [key, setKey] = useState(localStorage.getItem('modolrag-api-key') || ''); const [ok, setOk] = useState(false)
  useEffect(() => { api.getSettings().then(setS).catch(() => {}) }, [])
  const save = async () => { await api.updateSettings({ chunk_size: s.chunk_size, chunk_overlap: s.chunk_overlap, embedding_model: s.embedding_model, similarity_top_k: s.similarity_top_k, similarity_threshold: s.similarity_threshold }); localStorage.setItem('modolrag-api-key', key); setOk(true); setTimeout(() => setOk(false), 2000) }
  const up = (k: string, v: any) => setS(p => ({ ...p, [k]: v }))
  const ic = "w-full px-3 py-2.5 border border-slate-300 dark:border-zinc-600 rounded-lg text-sm bg-white dark:bg-zinc-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"

  return (<div className="max-w-lg">
    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">{t('settings.title')}</h2>
    <div className="space-y-5">
      <F l={t('settings.api_key')} h={t('settings.api_hint')}><input type="password" value={key} onChange={e => setKey(e.target.value)} className={ic} /></F>
      <F l={t('settings.chunk_size')}><input type="number" value={s.chunk_size || 512} onChange={e => up('chunk_size', +e.target.value)} className={ic} min={128} max={4096} /></F>
      <F l={t('settings.chunk_overlap')}><input type="number" value={s.chunk_overlap || 51} onChange={e => up('chunk_overlap', +e.target.value)} className={ic} min={0} max={512} /></F>
      <F l={t('settings.model')}><input value={s.embedding_model || 'nomic-embed-text'} onChange={e => up('embedding_model', e.target.value)} className={ic} /></F>
      <F l={`${t('settings.top_k')}: ${s.similarity_top_k || 5}`}><input type="range" min={1} max={50} value={s.similarity_top_k || 5} onChange={e => up('similarity_top_k', +e.target.value)} className="w-full accent-indigo-500" /></F>
      <F l={`${t('settings.threshold')}: ${s.similarity_threshold || 0.7}`}><input type="range" min={0} max={1} step={0.05} value={s.similarity_threshold || 0.7} onChange={e => up('similarity_threshold', +e.target.value)} className="w-full accent-indigo-500" /></F>
      <div className="flex items-center gap-3 pt-2">
        <button onClick={save} className="px-5 py-2.5 bg-slate-900 dark:bg-indigo-600 text-white rounded-lg text-sm hover:bg-slate-700 dark:hover:bg-indigo-500 font-medium transition-colors">{t('settings.save')}</button>
        {ok && <span className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">{t('settings.saved')}</span>}
      </div>
    </div>
  </div>)
}

function F({ l, h, children }: { l: string; h?: string; children: React.ReactNode }) {
  return <div><label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{l}</label>{h && <p className="text-[11px] text-slate-400 dark:text-zinc-500 mb-1.5">{h}</p>}{children}</div>
}
