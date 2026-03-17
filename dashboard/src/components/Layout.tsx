import { NavLink, Outlet } from 'react-router-dom'
import { useI18n } from '../i18n'
import { useTheme } from '../theme'

type TKey = Parameters<ReturnType<typeof useI18n>['t']>[0]

const navItems: { to: string; labelKey: TKey; icon: string }[] = [
  { to: '/documents', labelKey: 'nav.documents', icon: '\u{1F4C4}' },
  { to: '/collections', labelKey: 'nav.collections', icon: '\u{1F4DA}' },
  { to: '/search', labelKey: 'nav.search', icon: '\u{1F50D}' },
  { to: '/graph', labelKey: 'nav.graph', icon: '\u{1F578}\uFE0F' },
  { to: '/settings', labelKey: 'nav.settings', icon: '\u2699\uFE0F' },
]

export default function Layout() {
  const { locale, setLocale, t } = useI18n()
  const { theme, toggle } = useTheme()

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-zinc-900 transition-colors">
      <aside className="w-60 bg-slate-900 dark:bg-zinc-950 text-white flex flex-col border-r border-slate-800 dark:border-zinc-800">
        <div className="p-5 border-b border-slate-700 dark:border-zinc-800">
          <h1 className="text-lg font-bold tracking-tight">ModolRAG</h1>
          <p className="text-[11px] text-slate-400 mt-1 tracking-wide uppercase">Hybrid RAG Engine</p>
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map(item => (
            <NavLink key={item.to} to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all ${
                  isActive ? 'bg-indigo-600/20 text-indigo-300 border-l-2 border-indigo-400' : 'text-slate-400 hover:bg-slate-800 dark:hover:bg-zinc-800 hover:text-white'
                }`}>
              <span className="text-base">{item.icon}</span>
              <span>{t(item.labelKey)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-700 dark:border-zinc-800 space-y-1">
          <p className="px-3 text-[10px] text-slate-500 uppercase tracking-widest">{t('nav.api')}</p>
          <a href="/docs" target="_blank" rel="noopener noreferrer" className="block px-3 py-2 rounded-lg text-[13px] text-slate-500 hover:bg-slate-800 hover:text-slate-300 transition-all">Swagger</a>
          <a href="/redoc" target="_blank" rel="noopener noreferrer" className="block px-3 py-2 rounded-lg text-[13px] text-slate-500 hover:bg-slate-800 hover:text-slate-300 transition-all">ReDoc</a>
        </div>
        <div className="p-3 border-t border-slate-700 dark:border-zinc-800 flex items-center gap-2">
          <button onClick={() => setLocale(locale === 'ko' ? 'en' : 'ko')} className="flex-1 text-[11px] px-2 py-1.5 rounded-md bg-slate-800 dark:bg-zinc-800 text-slate-300 hover:bg-slate-700 transition-all font-medium">{locale === 'ko' ? 'EN' : 'KO'}</button>
          <button onClick={toggle} className="flex-1 text-[11px] px-2 py-1.5 rounded-md bg-slate-800 dark:bg-zinc-800 text-slate-300 hover:bg-slate-700 transition-all">{theme === 'light' ? '\u{1F319} Dark' : '\u2600\uFE0F Light'}</button>
        </div>
        <div className="px-5 py-3 text-[10px] text-slate-600">v0.1.0</div>
      </aside>
      <main className="flex-1 overflow-y-auto p-8"><Outlet /></main>
    </div>
  )
}
