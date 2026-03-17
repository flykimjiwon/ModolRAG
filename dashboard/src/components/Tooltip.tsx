import { useState, useRef, type ReactNode } from 'react'

interface Props {
  text: string
  children: ReactNode
  position?: 'top' | 'right' | 'bottom' | 'left'
}

export default function Tooltip({ text, children, position = 'top' }: Props) {
  const [show, setShow] = useState(false)
  const timer = useRef<number | null>(null)

  const pos = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  }[position]

  const arrow = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-zinc-800',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-zinc-800',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-zinc-800',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-zinc-800',
  }[position]

  const onEnter = () => { timer.current = window.setTimeout(() => setShow(true), 300) }
  const onLeave = () => { if (timer.current !== null) window.clearTimeout(timer.current); setShow(false) }

  return (
    <span className="relative inline-flex items-center" onMouseEnter={onEnter} onMouseLeave={onLeave}>
      {children}
      {show && (
        <span className={`absolute z-50 pointer-events-none ${pos}`}>
          <span className="block max-w-[240px] px-3 py-2 text-xs text-white bg-zinc-800 rounded-xl shadow-lg leading-relaxed whitespace-normal">{text}</span>
          <span className={`absolute w-0 h-0 border-4 ${arrow}`} />
        </span>
      )}
    </span>
  )
}

export function InfoIcon({ tip, position }: { tip: string; position?: 'top' | 'right' | 'bottom' | 'left' }) {
  return (
    <Tooltip text={tip} position={position}>
      <span className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold bg-slate-200 dark:bg-zinc-700 text-slate-500 dark:text-zinc-400 cursor-help ml-1 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors select-none">?</span>
    </Tooltip>
  )
}
