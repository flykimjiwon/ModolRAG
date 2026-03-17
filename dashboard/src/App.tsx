import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Documents from './pages/Documents'
import Search from './pages/Search'
import Graph from './pages/Graph'
import Settings from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter basename="/dashboard">
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/documents" replace />} />
          <Route path="documents" element={<Documents />} />
          <Route path="search" element={<Search />} />
          <Route path="graph" element={<Graph />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
