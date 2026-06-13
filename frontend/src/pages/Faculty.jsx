import { useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, BarChart3, FileText, Zap, BookOpen, ChevronRight } from 'lucide-react'
import FacultyDashboard from '../components/FacultyDashboard'
import COPOMatrix from '../components/COPOMatrix'
import NAACReport from '../components/NAACReport'
import AdminTraces from '../components/AdminTraces'

const sidebarItems = [
  { id: 'upload', label: 'Upload Questions', icon: <Upload size={16} /> },
  { id: 'copo', label: 'CO-PO Matrix', icon: <BarChart3 size={16} /> },
  { id: 'naac', label: 'NAAC Report', icon: <FileText size={16} /> },
  { id: 'traces', label: 'AI Traces', icon: <Zap size={16} /> },
]

export default function Faculty() {
  const [activeTab, setActiveTab] = useState('upload')
  const [courseId, setCourseId] = useState('CS301')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-[calc(100vh-64px)] flex">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } transition-all duration-300 border-r border-brand-border bg-brand-card flex flex-col py-6 shrink-0`}
      >
        <div className="px-4 mb-6 flex items-center justify-between">
          {sidebarOpen && (
            <div>
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-1">Course</div>
              <input
                value={courseId}
                onChange={(e) => setCourseId(e.target.value)}
                className="input text-sm py-1.5 px-2"
                placeholder="Course ID"
              />
            </div>
          )}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors ml-auto"
          >
            <ChevronRight
              size={16}
              className={`transition-transform duration-300 ${sidebarOpen ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        <nav className="flex flex-col gap-1 px-2">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''} ${
                !sidebarOpen ? 'justify-center px-2' : ''
              }`}
              title={!sidebarOpen ? item.label : ''}
            >
              {item.icon}
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        {sidebarOpen && (
          <div className="mt-auto px-4">
            <div className="card p-3">
              <div className="flex items-center gap-2 mb-1.5">
                <BookOpen size={12} className="text-brand-orange" />
                <span className="text-xs font-semibold text-brand-amber">NBA Tip</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                At least 30% of questions should target Analyze/Evaluate/Create levels.
              </p>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6 md:p-8">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'upload' && <FacultyDashboard courseId={courseId} />}
          {activeTab === 'copo' && <COPOMatrix courseId={courseId} />}
          {activeTab === 'naac' && <NAACReport courseId={courseId} />}
          {activeTab === 'traces' && <AdminTraces />}
        </motion.div>
      </main>
    </div>
  )
}
