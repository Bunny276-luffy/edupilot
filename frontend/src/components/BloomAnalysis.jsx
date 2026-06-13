import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const classifyWithGemini = async (questions) => {
  const prompt = `Classify each question into Bloom's Taxonomy levels (Remember, Understand, Apply, Analyze, Evaluate, Create). Return JSON array: [{question, level, reasoning}]\n\nQuestions:\n${questions.join('\n')}`;
  
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`,
    {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.3, maxOutputTokens: 1000 }
      })
    }
  );
  if (!response.ok) {
    throw new Error(`Gemini API error: ${response.status}`);
  }
  const data = await response.json();
  const text = data.candidates[0].content.parts[0].text;
  const clean = text.replace(/```json|```/g, '').trim();
  return JSON.parse(clean);
};

// ── Backend-first helper ──────────────────────────────────────────────────────
export const classifyWithBackend = async (formData) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(`${API_BASE}/faculty/upload-questions`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        course_id: formData.course_id,
        questions_text: formData.questions_text,
      }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`Backend error: ${res.status}`);
    return await res.json(); // { classified, total, warning, suggestions }
  } finally {
    clearTimeout(timer);
  }
};


const BLOOM_COLORS = {
  Remember: '#94a3b8',
  Understand: '#60a5fa',
  Apply: '#34d399',
  Analyze: '#a78bfa',
  Evaluate: '#f59e0b',
  Create: '#f87171',
}

const BLOOMS_ORDER = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']

function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const d = payload[0].payload
    return (
      <div className="bg-brand-card border border-brand-border rounded-xl px-4 py-3 shadow-2xl">
        <p className="font-semibold text-white">{d.level}</p>
        <p className="text-slate-400 text-sm">
          {d.count} question{d.count !== 1 ? 's' : ''} — {d.percentage}%
        </p>
      </div>
    )
  }
  return null
}

export default function BloomAnalysis({ distribution = [], total = 0 }) {
  // Ensure all levels are present with at least 0
  const fullDist = BLOOMS_ORDER.map((level) => {
    const found = distribution.find((d) => d.level === level)
    return found || { level, count: 0, percentage: 0 }
  })

  const nonZero = fullDist.filter((d) => d.count > 0)

  const highOrder = fullDist
    .filter((d) => ['Analyze', 'Evaluate', 'Create'].includes(d.level))
    .reduce((sum, d) => sum + d.count, 0)

  const highOrderPct = total > 0 ? Math.round((highOrder / total) * 100) : 0

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-display font-bold text-xl text-white">Bloom's Taxonomy Analysis</h3>
          <p className="text-slate-400 text-sm mt-0.5">
            {total} question{total !== 1 ? 's' : ''} classified
          </p>
        </div>
        <div
          className={`text-center px-4 py-2 rounded-xl border ${
            highOrderPct >= 30
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}
        >
          <div className="font-black text-2xl">{highOrderPct}%</div>
          <div className="text-xs font-medium">Higher-Order</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={nonZero.length > 0 ? nonZero : [{ level: 'No Data', count: 1, percentage: 100 }]}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={3}
                dataKey="count"
                nameKey="level"
              >
                {nonZero.map((entry) => (
                  <Cell
                    key={entry.level}
                    fill={BLOOM_COLORS[entry.level] || '#475569'}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value) => (
                  <span style={{ color: BLOOM_COLORS[value] || '#94a3b8', fontSize: '12px' }}>
                    {value}
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={fullDist} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="level"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {fullDist.map((entry) => (
                  <Cell key={entry.level} fill={BLOOM_COLORS[entry.level] || '#475569'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Level badges */}
      <div className="flex flex-wrap gap-2 mt-5">
        {fullDist.map((d) => (
          <div
            key={d.level}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium`}
            style={{
              backgroundColor: `${BLOOM_COLORS[d.level]}15`,
              borderColor: `${BLOOM_COLORS[d.level]}40`,
              color: BLOOM_COLORS[d.level],
            }}
          >
            <span className="font-bold">{d.level}</span>
            <span className="opacity-75">
              {d.count} ({d.percentage}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
