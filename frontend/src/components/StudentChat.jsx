import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, Loader2, Brain, BookOpen, Circle } from 'lucide-react'

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// ── Backend-first helper ──────────────────────────────────────────────────────
const callBackendChat = async (payload) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const res = await fetch(`${API_BASE}/student/chat`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`Backend error: ${res.status}`);
    return await res.json(); // { session_id, reply, understanding_level, exchange_count }
  } finally {
    clearTimeout(timer);
  }
};

// ── Gemini direct helper (kept exactly as-is) ─────────────────────────────────
const callGeminiDirect = async (userMessage, topic) => {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system_instruction: {
          parts: [{ text: "You are a Socratic tutor. Never give direct answers. Guide the student with probing questions. After 3 exchanges, if still stuck, give a hint. End every response with [LEVEL: Struggling], [LEVEL: Getting It], or [LEVEL: Mastered] based on student understanding." }]
        },
        contents: [{ parts: [{ text: userMessage }] }],
        generationConfig: { temperature: 0.7, maxOutputTokens: 500 }
      })
    }
  );
  if (!response.ok) {
    throw new Error(`Gemini API error: ${response.status}`);
  }
  const data = await response.json();
  return data.candidates[0].content.parts[0].text;
};

const levelColors = {
  Struggling: 'text-red-400',
  'Getting It': 'text-yellow-400',
  Mastered: 'text-green-400',
}

const levelBadge = {
  Struggling: 'badge-struggling',
  'Getting It': 'badge-getting-it',
  Mastered: 'badge-mastered',
}

const TOPICS = [
  'Binary Trees',
  'Normalization',
  'Sorting Algorithms',
  'Hash Tables',
  'Graph Traversal',
  'SQL Joins',
  'OS Scheduling',
  'Recursion',
]

export default function StudentChat({ studentId }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hi! I'm your Socratic tutor. I won't give you direct answers — instead I'll guide you to discover the concepts yourself.\n\nWhat topic would you like to explore today? You can pick from the suggestions or type your own.",
    },
  ])
  const [input, setInput] = useState('')
  const [topic, setTopic] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [understanding, setUnderstanding] = useState(null)
  const [exchangeCount, setExchangeCount] = useState(0)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    // Use first message as topic if not set
    const currentTopic = topic || text.substring(0, 60)
    if (!topic) setTopic(currentTopic)

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    // ── Backend first, Gemini direct as fallback ──────────────────────────────
    try {
      const payload = {
        student_id: studentId,
        topic: currentTopic,
        message: text,
        session_id: sessionId,
      };
      const data = await callBackendChat(payload);
      console.log('[Chat] backend');

      // Backend format: { session_id, reply, understanding_level, exchange_count }
      setSessionId(data.session_id || ('backend-' + Date.now()));
      setUnderstanding(data.understanding_level || 'Struggling');
      setExchangeCount(data.exchange_count ?? (exchangeCount + 1));
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (backendErr) {
      // ── Fallback: Gemini direct ──────────────────────────────────────────────
      try {
        const reply = await callGeminiDirect(text, currentTopic);
        console.log('[Chat] gemini-direct');

        let cleanedReply = reply;
        let level = 'Struggling';

        if (reply.includes('[LEVEL:')) {
          const parts = reply.split('[LEVEL:');
          cleanedReply = parts[0].trim();
          const levelRaw = parts[1].replace(']', '').trim();
          if (['Struggling', 'Getting It', 'Mastered'].includes(levelRaw)) {
            level = levelRaw;
          }
        }

        // Gemini direct format: { reply, understanding_level } (no session_id)
        setSessionId((prev) => prev || 'direct-' + Date.now());
        setUnderstanding(level);
        setExchangeCount((prev) => prev + 1);
        setMessages((prev) => [...prev, { role: 'assistant', content: cleanedReply }]);
      } catch (geminiErr) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: "I couldn't connect to the AI service. Please make sure the backend is running.",
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const startTopic = (t) => {
    setTopic(t)
    setInput(`Tell me about ${t}`)
  }

  const resetChat = () => {
    setMessages([
      {
        role: 'assistant',
        content:
          "Let's start fresh! What topic would you like to explore?",
      },
    ])
    setTopic('')
    setSessionId(null)
    setUnderstanding(null)
    setExchangeCount(0)
    setInput('')
  }

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-130px)] flex gap-4 p-4">
      {/* Progress sidebar */}
      <aside className="hidden lg:flex w-52 flex-col gap-3 shrink-0">
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Brain size={15} className="text-brand-orange" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Current Session
            </span>
          </div>
          {topic && (
            <div className="text-sm font-semibold text-white mb-2 truncate" title={topic}>
              {topic}
            </div>
          )}
          {understanding && (
            <span className={`badge ${levelBadge[understanding] || 'badge-struggling'}`}>
              <Circle size={6} fill="currentColor" />
              {understanding}
            </span>
          )}
          {exchangeCount > 0 && (
            <div className="text-xs text-slate-500 mt-2">{exchangeCount} exchanges</div>
          )}
          {(topic || understanding) && (
            <button
              onClick={resetChat}
              className="mt-3 text-xs text-slate-500 hover:text-slate-300 transition-colors underline"
            >
              Start new topic
            </button>
          )}
        </div>

        <div className="card p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Quick Topics
          </div>
          <div className="flex flex-col gap-1">
            {TOPICS.map((t) => (
              <button
                key={t}
                onClick={() => startTopic(t)}
                className="text-left text-xs text-slate-400 hover:text-brand-amber py-1.5 px-2 rounded-lg hover:bg-brand-orange/10 transition-colors"
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex-1 flex flex-col card overflow-hidden">
        {/* Header */}
        <div className="px-5 py-3 border-b border-brand-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-orange to-orange-700 flex items-center justify-center">
              <Brain size={14} className="text-white" />
            </div>
            <div>
              <span className="font-semibold text-sm text-white">Socratic Tutor</span>
              {topic && <span className="text-xs text-slate-500 ml-2">— {topic}</span>}
            </div>
          </div>
          {understanding && (
            <span className={`badge ${levelBadge[understanding] || 'badge-struggling'} text-xs`}>
              <Circle size={5} fill="currentColor" />
              {understanding}
            </span>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} animate-slide-up`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                  msg.role === 'user'
                    ? 'bg-brand-orange text-white'
                    : 'bg-brand-blue text-white'
                }`}
              >
                {msg.role === 'user' ? 'U' : 'AI'}
              </div>

              {/* Bubble */}
              <div
                className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user' ? 'chat-bubble-user text-white' : 'chat-bubble-ai text-slate-200'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      strong: ({ children }) => (
                        <strong className="text-brand-amber font-semibold">{children}</strong>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="w-7 h-7 rounded-full bg-brand-blue flex items-center justify-center text-xs font-bold shrink-0">
                AI
              </div>
              <div className="chat-bubble-ai px-4 py-3">
                <div className="flex items-center gap-1">
                  {[0, 0.15, 0.3].map((d, i) => (
                    <div
                      key={i}
                      className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"
                      style={{ animationDelay: `${d}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 pb-4 pt-3 border-t border-brand-border">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={2}
              className="input resize-none flex-1 text-sm"
              placeholder="Ask a question or name a topic… (Enter to send)"
              disabled={loading}
              id="chat-input"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="btn-primary w-11 h-11 p-0 flex items-center justify-center shrink-0"
              id="btn-send-chat"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2">
            The tutor will guide you with questions. After 3 exchanges, hints are unlocked.
          </p>
        </div>
      </div>
    </div>
  )
}
