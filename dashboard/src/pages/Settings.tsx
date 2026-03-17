import { useState, useEffect } from 'react'
import { api } from '../api'

export default function Settings() {
  const [settings, setSettings] = useState<Record<string, any>>({})
  const [apiKey, setApiKey] = useState(localStorage.getItem('modolrag-api-key') || '')
  const [saved, setSaved] = useState(false)

  useEffect(() => { api.getSettings().then(setSettings).catch(() => {}) }, [])

  const onSave = async () => {
    await api.updateSettings({
      chunk_size: settings.chunk_size,
      chunk_overlap: settings.chunk_overlap,
      embedding_model: settings.embedding_model,
      similarity_top_k: settings.similarity_top_k,
      similarity_threshold: settings.similarity_threshold,
    })
    localStorage.setItem('modolrag-api-key', apiKey)
    setSaved(true); setTimeout(() => setSaved(false), 2000)
  }

  const update = (key: string, val: any) => setSettings(s => ({ ...s, [key]: val }))

  return (
    <div className="max-w-lg">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Settings</h2>
      <div className="space-y-4">
        <Field label="API Key" hint="Stored in browser localStorage">
          <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm" placeholder="Your API key" />
        </Field>
        <Field label="Chunk Size" hint="128-4096">
          <input type="number" value={settings.chunk_size || 512} onChange={e => update('chunk_size', +e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm" min={128} max={4096} />
        </Field>
        <Field label="Chunk Overlap" hint="0-512">
          <input type="number" value={settings.chunk_overlap || 51} onChange={e => update('chunk_overlap', +e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm" min={0} max={512} />
        </Field>
        <Field label="Embedding Model">
          <input value={settings.embedding_model || 'nomic-embed-text'} onChange={e => update('embedding_model', e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm" />
        </Field>
        <Field label={`Similarity Top-K: ${settings.similarity_top_k || 5}`}>
          <input type="range" min={1} max={50} value={settings.similarity_top_k || 5} onChange={e => update('similarity_top_k', +e.target.value)} className="w-full" />
        </Field>
        <Field label={`Similarity Threshold: ${settings.similarity_threshold || 0.7}`}>
          <input type="range" min={0} max={1} step={0.05} value={settings.similarity_threshold || 0.7} onChange={e => update('similarity_threshold', +e.target.value)} className="w-full" />
        </Field>
        <button onClick={onSave} className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm hover:bg-gray-700">
          Save Settings
        </button>
        {saved && <span className="text-sm text-green-600 ml-3">Saved!</span>}
      </div>
    </div>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-400 mb-1">{hint}</p>}
      {children}
    </div>
  )
}
