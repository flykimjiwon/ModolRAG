const API_BASE = '/api'

function getApiKey(): string {
  return localStorage.getItem('modolrag-api-key') || ''
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)
  const key = getApiKey()
  if (key) headers.set('X-API-Key', key)
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}

export const api = {
  getDocuments: () => apiFetch('/documents'),
  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const headers: Record<string, string> = {}
    const key = getApiKey()
    if (key) headers['X-API-Key'] = key
    return fetch(`${API_BASE}/ingest`, { method: 'POST', headers, body: form }).then(r => r.json())
  },
  deleteDocument: (id: string) => apiFetch(`/documents/${id}`, { method: 'DELETE' }),
  search: (query: string, mode: string, topK: number) =>
    apiFetch('/search', { method: 'POST', body: JSON.stringify({ query, mode, top_k: topK }) }),
  getGraph: (ns = 'default') => apiFetch(`/graph?namespace=${ns}`),
  getSettings: () => apiFetch('/settings'),
  updateSettings: (data: Record<string, unknown>) =>
    apiFetch('/settings', { method: 'PUT', body: JSON.stringify(data) }),
}
