import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BookOpen,
  GraduationCap,
  BarChart3,
  FileText,
  Search,
  Brain,
  ArrowRight,
  Sparkles,
  Shield,
  Zap,
} from 'lucide-react'

const features = [
  {
    icon: <BarChart3 size={22} />,
    title: "Bloom's Analyzer",
    desc: 'Auto-classify questions by cognitive level with NBA compliance warnings.',
    color: 'from-purple-500 to-indigo-600',
    glow: 'shadow-purple-500/20',
  },
  {
    icon: <FileText size={22} />,
    title: 'CO-PO Matrix',
    desc: 'Vector-search-powered course outcome to program outcome mapping.',
    color: 'from-blue-500 to-cyan-600',
    glow: 'shadow-blue-500/20',
  },
  {
    icon: <Shield size={22} />,
    title: 'NAAC Reports',
    desc: 'One-click accreditation-ready PDF reports for faculty.',
    color: 'from-green-500 to-emerald-600',
    glow: 'shadow-green-500/20',
  },
  {
    icon: <Brain size={22} />,
    title: 'Socratic Tutor',
    desc: 'AI guide that never gives answers — helps students discover knowledge.',
    color: 'from-orange-500 to-red-500',
    glow: 'shadow-orange-500/20',
  },
  {
    icon: <Search size={22} />,
    title: 'Past Papers Search',
    desc: 'Full-text Elasticsearch search across university question banks.',
    color: 'from-yellow-500 to-orange-500',
    glow: 'shadow-yellow-500/20',
  },
  {
    icon: <Zap size={22} />,
    title: 'AI Tracing',
    desc: 'Arize Phoenix traces every Gemini call — latency, tokens, and more.',
    color: 'from-pink-500 to-rose-600',
    glow: 'shadow-pink-500/20',
  },
]

const stats = [
  { value: '6', label: 'AI-Powered Features' },
  { value: '100%', label: 'NAAC Compliant' },
  { value: '<2s', label: 'Analysis Time' },
  { value: '∞', label: 'Question Papers' },
]

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden py-20 md:py-32 px-4">
        {/* Background glows */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-blue/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-brand-orange/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-5xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 bg-brand-orange/10 border border-brand-orange/30 text-brand-amber text-sm font-semibold px-4 py-2 rounded-full mb-8"
          >
            <Sparkles size={14} />
            AI-Powered Academic Agent for Indian Colleges
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display font-black text-5xl md:text-7xl leading-tight mb-6"
          >
            From Classroom
            <br />
            <span className="gradient-text">to NAAC</span>
            <br />
            <span className="text-white">— Automated.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-12 leading-relaxed"
          >
            EduPilot uses Gemini 1.5 Pro to automate Bloom's taxonomy analysis, CO-PO mapping,
            and NAAC report generation — while giving students a Socratic AI tutor.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
          >
            <Link
              to="/faculty"
              id="cta-faculty"
              className="group flex items-center gap-3 bg-gradient-to-r from-brand-blue to-brand-indigo hover:from-brand-indigo hover:to-brand-light text-white font-semibold px-8 py-4 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/25 hover:-translate-y-1 w-full sm:w-auto justify-center"
            >
              <BookOpen size={20} />
              I am a Faculty
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/student"
              id="cta-student"
              className="group flex items-center gap-3 bg-gradient-to-r from-brand-orange to-orange-700 hover:from-orange-600 hover:to-orange-800 text-white font-semibold px-8 py-4 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-orange-500/25 hover:-translate-y-1 w-full sm:w-auto justify-center"
            >
              <GraduationCap size={20} />
              I am a Student
              <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {stats.map((s, i) => (
              <div
                key={i}
                className="card p-5 text-center hover:border-brand-orange/40 transition-colors duration-300"
              >
                <div className="font-display font-black text-3xl gradient-text mb-1">{s.value}</div>
                <div className="text-slate-400 text-sm">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 border-t border-brand-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="font-display font-bold text-3xl md:text-4xl text-white mb-4">
              Everything you need for
              <span className="gradient-text"> accreditation & learning</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Six deeply integrated AI features covering the entire academic quality lifecycle.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className={`card p-6 group hover:border-white/20 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${f.glow}`}
              >
                <div
                  className={`w-11 h-11 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center text-white mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}
                >
                  {f.icon}
                </div>
                <h3 className="font-display font-bold text-lg text-white mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="py-20 px-4 border-t border-brand-border">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-display font-bold text-3xl text-white text-center mb-12">
            Powered by Enterprise-Grade Stack
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'Gemini 1.5 Pro', role: 'AI Engine', color: 'text-blue-400' },
              { name: 'MongoDB Atlas', role: 'Vector DB', color: 'text-green-400' },
              { name: 'Elasticsearch', role: 'Search', color: 'text-yellow-400' },
              { name: 'Arize Phoenix', role: 'Tracing', color: 'text-pink-400' },
              { name: 'FastAPI', role: 'Backend', color: 'text-teal-400' },
              { name: 'React + Vite', role: 'Frontend', color: 'text-cyan-400' },
              { name: 'ReportLab', role: 'PDF', color: 'text-orange-400' },
              { name: 'Cloud Run', role: 'Deploy', color: 'text-purple-400' },
            ].map((t, i) => (
              <div key={i} className="card p-4 text-center hover:border-brand-border/80">
                <div className={`font-semibold text-sm ${t.color} mb-1`}>{t.name}</div>
                <div className="text-xs text-slate-500">{t.role}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-brand-border py-8 px-4 text-center text-slate-500 text-sm">
        <p>EduPilot © 2024 — MIT License — Built for Indian Higher Education</p>
      </footer>
    </main>
  )
}
