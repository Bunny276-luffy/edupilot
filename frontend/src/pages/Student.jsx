import { useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, Search, BookOpen, TrendingUp, Circle } from 'lucide-react'
import StudentChat from '../components/StudentChat'
import PaperSearch from '../components/PaperSearch'

const DEMO_STUDENT = {
  id: '60c72b2f9b1d8e1f5c8f8b8a',
  name: 'Rahul Sharma',
}

const levelBadge = {
  Struggling: 'badge-struggling',
  'Getting It': 'badge-getting-it',
  Mastered: 'badge-mastered',
}

export default function Student() {
  const [activePanel, setActivePanel] = useState('chat')
  const [studentId] = useState(DEMO_STUDENT.id)

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col">
      {/* Panel toggle bar */}
      <div className="border-b border-brand-border bg-brand-card px-4 py-3 shrink-0">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <div className="flex gap-2">
            {[
              { id: 'chat',   label: '🧠 Tutor Chat' },
              { id: 'search', label: '🔍 Past Papers' },
            ].map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setActivePanel(id)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activePanel === id
                    ? 'bg-brand-orange/20 text-brand-amber border border-brand-orange/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <span className="text-xs text-slate-500 ml-auto hidden sm:block">
            {DEMO_STUDENT.name} — Socratic Learning Mode
          </span>
        </div>
      </div>

      {/* Content — grid layout: chat (3/4) + progress sidebar (1/4) on large screens */}
      <div className="flex-1 overflow-hidden">
        {activePanel === 'chat' ? (
          <motion.div
            key="chat"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            <StudentChat studentId={studentId} />
          </motion.div>
        ) : (
          <motion.div
            key="search"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="h-full overflow-auto"
          >
            {/* On large screens: show progress sidebar alongside search */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-7xl mx-auto p-4 md:p-6">
              {/* Paper search — 3 cols */}
              <div className="lg:col-span-3">
                <PaperSearch />
              </div>

              {/* Progress sidebar — 1 col, hidden on small */}
              <aside className="hidden lg:flex lg:col-span-1 flex-col gap-4">
                <div className="card p-4 animate-fade-in-up">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp size={15} className="text-brand-orange" />
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      My Progress
                    </span>
                  </div>
                  <div className="flex flex-col gap-2">
                    {[
                      { topic: 'Binary Search Trees', level: 'Getting It' },
                      { topic: 'Sorting Algorithms',  level: 'Struggling' },
                    ].map(({ topic, level }) => (
                      <div
                        key={topic}
                        className="p-3 bg-brand-surface rounded-xl border border-brand-border"
                      >
                        <div className="text-xs text-slate-200 font-medium mb-1.5 truncate" title={topic}>
                          {topic}
                        </div>
                        <span className={`badge ${levelBadge[level] || 'badge-struggling'} text-xs`}>
                          <Circle size={5} fill="currentColor" />
                          {level}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen size={14} className="text-brand-amber" />
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Study Tip
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Use the Tutor Chat to deepen understanding before searching past papers. Socratic questioning builds lasting knowledge.
                  </p>
                </div>
              </aside>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
