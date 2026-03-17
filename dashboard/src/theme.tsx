import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

type Theme = 'light' | 'dark'
interface Ctx { theme: Theme; toggle: () => void }
const ThemeCtx = createContext<Ctx>({ theme: 'light', toggle: () => {} })

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('modolrag-theme') as Theme) || 'light')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('modolrag-theme', theme)
  }, [theme])

  return <ThemeCtx.Provider value={{ theme, toggle: () => setTheme(t => t === 'light' ? 'dark' : 'light') }}>{children}</ThemeCtx.Provider>
}

export const useTheme = () => useContext(ThemeCtx)
