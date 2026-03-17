import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/documents', label: 'Documents', icon: '\u{1F4C4}' },
  { to: '/search', label: 'Search', icon: '\u{1F50D}' },
  { to: '/graph', label: 'Graph', icon: '\u{1F578}\uFE0F' },
  { to: '/settings', label: 'Settings', icon: '\u2699\uFE0F' },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-56 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-lg font-semibold">ModolRAG</h1>
          <p className="text-xs text-gray-400 mt-1">Hybrid RAG Engine</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700 text-xs text-gray-500">v0.1.0</div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
