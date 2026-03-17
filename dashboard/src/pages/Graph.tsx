import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

interface Node { id: string; title: string; node_type: string; content?: string }
interface Edge { source_id: string; target_id: string; relation_type: string }
const C: Record<string, string> = { person: '#3b82f6', org: '#22c55e', concept: '#a855f7', location: '#f97316', event: '#ef4444', document: '#6b7280' }

export default function Graph() {
  const { t } = useI18n()
  const [nodes, setNodes] = useState<Node[]>([]); const [edges, setEdges] = useState<Edge[]>([])
  const [sel, setSel] = useState<Node | null>(null); const ref = useRef<HTMLDivElement>(null); const [FG, setFG] = useState<any>(null)
  useEffect(() => { import('react-force-graph-2d').then(m => setFG(() => m.default)) }, [])
  useEffect(() => { api.getGraph().then(d => { setNodes(d.nodes || []); setEdges(d.edges || []) }).catch(() => {}) }, [])
  const data = { nodes: nodes.map(n => ({ id: n.id, name: n.title, type: n.node_type, content: n.content })), links: edges.map(e => ({ source: e.source_id, target: e.target_id, label: e.relation_type })) }
  const click = useCallback((n: any) => setSel({ id: n.id, title: n.name, node_type: n.type, content: n.content }), [])

  return (<div>
    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8">{t('graph.title')}</h2>
    <div className="flex gap-4">
      <div ref={ref} className="flex-1 bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl overflow-hidden" style={{ height: 500 }}>
        {FG && nodes.length > 0 ? <FG graphData={data} nodeLabel="name" nodeColor={(n: any) => C[n.type] || '#6b7280'} nodeRelSize={6} linkLabel="label" linkDirectionalParticles={1} onNodeClick={click} backgroundColor="transparent" width={ref.current?.clientWidth || 600} height={500} />
          : <div className="flex items-center justify-center h-full text-slate-400 dark:text-zinc-500 text-sm">{nodes.length === 0 ? t('graph.empty') : t('graph.loading')}</div>}
      </div>
      {sel && <div className="w-64 bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl p-5">
        <h3 className="font-bold text-slate-900 dark:text-slate-100">{sel.title}</h3>
        <span className="text-[11px] px-2 py-0.5 rounded-full mt-2 inline-block font-medium" style={{ backgroundColor: (C[sel.node_type] || '#6b7280') + '20', color: C[sel.node_type] || '#6b7280' }}>{sel.node_type}</span>
        {sel.content && <p className="text-sm text-slate-600 dark:text-zinc-400 mt-3 leading-relaxed">{sel.content}</p>}
        <button onClick={() => setSel(null)} className="text-xs text-slate-400 mt-4 hover:text-slate-600 dark:hover:text-zinc-300">{t('graph.close')}</button>
      </div>}
    </div>
    <div className="flex gap-4 mt-3">{Object.entries(C).map(([ty, co]) => <span key={ty} className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-zinc-400"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: co }} /> {ty}</span>)}</div>
  </div>)
}
