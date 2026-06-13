import { Link, useLocation } from 'react-router-dom'
import { GraduationCap, BookOpen, LayoutDashboard, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function Navbar() {
  const { pathname } = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = [
    { to: '/', label: 'Home', icon: <LayoutDashboard size={16} /> },
    { to: '/faculty', label: 'Faculty', icon: <BookOpen size={16} /> },
    { to: '/student', label: 'Student', icon: <GraduationCap size={16} /> },
  ]

  return (
    <header className="sticky top-0 z-50 border-b border-brand-border bg-brand-surface/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-orange to-orange-700 flex items-center justify-center shadow-lg shadow-orange-500/25">
            <GraduationCap size={18} className="text-white" />
          </div>
          <span className="font-display font-bold text-xl text-white group-hover:text-brand-amber transition-colors">
            Edu<span className="text-brand-orange">Pilot</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                pathname === l.to
                  ? 'bg-brand-orange/20 text-brand-amber border border-brand-orange/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {l.icon}
              {l.label}
            </Link>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <span className="text-xs text-slate-500 font-medium">Powered by</span>
          <span className="text-xs font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-full">
            Gemini 1.5 Pro
          </span>
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 text-slate-400 hover:text-white"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-brand-border bg-brand-surface"
          >
            <div className="px-4 py-3 flex flex-col gap-1">
              {links.map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    pathname === l.to
                      ? 'bg-brand-orange/20 text-brand-amber'
                      : 'text-slate-400 hover:text-white hover:bg-white/10'
                  }`}
                >
                  {l.icon}
                  {l.label}
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
