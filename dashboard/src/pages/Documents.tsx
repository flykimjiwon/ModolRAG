import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

interface Doc { id: string; original_name: string; mime_type: string; status: string; chunk_count: number; created_at: string }

const statusColor: Record<string, string> = {
  uploaded: 'bg-gray-200 text-gray-700',
  processing: 'bg-yellow-100 text-yellow-800',
  vectorizing: 'bg-blue-100 text-blue-800',
  vectorized: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
}

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)

  const load = useCallback(() => {
    api.getDocuments().then(d => setDocs(d.documents || [])).catch(() => {})
  }, [])

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t) }, [load])

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try { await api.uploadDocument(file); load() } finally { setUploading(false); e.target.value = '' }
  }

  const onDelete = async (id: string) => {
    if (!confirm('Delete this document?')) return
    await api.deleteDocument(id); load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Documents</h2>
        <label className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm cursor-pointer hover:bg-gray-700">
          {uploading ? 'Uploading...' : 'Upload File'}
          <input type="file" className="hidden" onChange={onUpload} disabled={uploading} />
        </label>
      </div>
      {docs.length === 0 ? (
        <div className="text-center py-16 text-gray-400">No documents yet. Upload one to get started.</div>
      ) : (
        <table className="w-full text-sm">
          <thead><tr className="text-left text-gray-500 border-b">
            <th className="pb-2">Name</th><th className="pb-2">Type</th><th className="pb-2">Status</th><th className="pb-2">Chunks</th><th className="pb-2">Date</th><th className="pb-2"></th>
          </tr></thead>
          <tbody>
            {docs.map(d => (
              <tr key={d.id} className="border-b hover:bg-gray-50">
                <td className="py-2 font-medium text-gray-900">{d.original_name}</td>
                <td className="py-2 text-gray-500">{d.mime_type?.split('/').pop()}</td>
                <td className="py-2"><span className={`px-2 py-0.5 rounded-full text-xs ${statusColor[d.status] || 'bg-gray-100'}`}>{d.status}</span></td>
                <td className="py-2 text-gray-500">{d.chunk_count}</td>
                <td className="py-2 text-gray-400">{new Date(d.created_at).toLocaleDateString()}</td>
                <td className="py-2"><button onClick={() => onDelete(d.id)} className="text-red-500 hover:text-red-700 text-xs">Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
