import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface Props {
  onSubmit: (request: string) => void
  loading: boolean
}

const EXAMPLES = [
  'Research the latest AI agent frameworks, write a comparison table in Python, and fact-check the top 3 claims',
  'Analyze the pros and cons of microservices vs monolith architecture, then synthesize a recommendation',
  'Find recent news about quantum computing, analyze the key breakthroughs, and write an executive summary',
]

export function TaskInput({ onSubmit, loading }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || loading) return
    onSubmit(trimmed)
    setValue('')
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
        New Task
      </h2>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Describe a complex task that requires multiple capabilities..."
          rows={3}
          disabled={loading}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault()
              const trimmed = value.trim()
              if (trimmed && !loading) { onSubmit(trimmed); setValue('') }
            }
          }}
        />
        <button
          type="submit"
          disabled={!value.trim() || loading}
          className="px-5 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg font-medium text-sm transition-colors flex items-center gap-2 self-end"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          Submit
        </button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => setValue(ex)}
            disabled={loading}
            className="text-xs text-gray-500 hover:text-gray-300 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded px-2 py-1 transition-colors disabled:opacity-40 text-left"
          >
            {ex.slice(0, 60)}…
          </button>
        ))}
      </div>
    </div>
  )
}
