import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'

interface Node { id: string; title: string; node_type: string; content?: string }
interface Edge { source_id: string; target_id: string; relation_type: string; weight: number }

const typeColors: Record<string, string> = {
  person: '#3b82f6', org: '#22c55e', concept: '#a855f7', location: '#f97316', event: '#ef4444', document: '#6b7280',
}

export default function Graph() {
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selected, setSelected] = useState<Node | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [ForceGraph, setForceGraph] = useState<any>(null)

  useEffect(() => {
    import('react-force-graph-2d').then(m => setForceGraph(() => m.default))
  }, [])

  useEffect(() => {
    api.getGraph().then(data => {
      setNodes(data.nodes || [])
      setEdges(data.edges || [])
    }).catch(() => {})
  }, [])

  const graphData = {
    nodes: nodes.map(n => ({ id: n.id, name: n.title, type: n.node_type, content: n.content })),
    links: edges.map(e => ({ source: e.source_id, target: e.target_id, label: e.relation_type })),
  }

  const handleNodeClick = useCallback((node: any) => {
    setSelected({ id: node.id, title: node.name, node_type: node.type, content: node.content })
  }, [])

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Knowledge Graph</h2>
      <div className="flex gap-4">
        <div ref={containerRef} className="flex-1 border rounded-md bg-white" style={{ height: 500 }}>
          {ForceGraph && nodes.length > 0 ? (
            <ForceGraph
              graphData={graphData}
              nodeLabel="name"
              nodeColor={(n: any) => typeColors[n.type] || '#6b7280'}
              nodeRelSize={6}
              linkLabel="label"
              linkDirectionalParticles={1}
              onNodeClick={handleNodeClick}
              width={containerRef.current?.clientWidth || 600}
              height={500}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              {nodes.length === 0 ? 'No graph data. Ingest documents to build the knowledge graph.' : 'Loading...'}
            </div>
          )}
        </div>
        {selected && (
          <div className="w-64 border rounded-md p-4 bg-white">
            <h3 className="font-semibold text-gray-900">{selected.title}</h3>
            <span className="text-xs px-2 py-0.5 rounded-full mt-1 inline-block" style={{ backgroundColor: typeColors[selected.node_type] + '20', color: typeColors[selected.node_type] }}>{selected.node_type}</span>
            {selected.content && <p className="text-sm text-gray-600 mt-3">{selected.content}</p>}
            <button onClick={() => setSelected(null)} className="text-xs text-gray-400 mt-4 hover:text-gray-600">Close</button>
          </div>
        )}
      </div>
      <div className="flex gap-3 mt-3">
        {Object.entries(typeColors).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1 text-xs text-gray-500">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} /> {type}
          </span>
        ))}
      </div>
    </div>
  )
}
