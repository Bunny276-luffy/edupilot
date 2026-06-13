import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Faculty from './pages/Faculty'
import Student from './pages/Student'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-brand-surface text-slate-100 font-sans">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/faculty" element={<Faculty />} />
          <Route path="/student" element={<Student />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
