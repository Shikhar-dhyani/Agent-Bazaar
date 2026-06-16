import { useState } from 'react'
import { CheckCircle2, Circle, Clock, Loader2, XCircle, Zap, ChevronDown, ChevronRight } from 'lucide-react'
import type { Subtask, SubtaskStatus, Bid, Capability } from '../types'

const CAPABILITY_COLORS: Record<Capability, string> = {
  web_search: 'bg-blue-900 text-blue-300 border-blue-700',
  code_generation: 'bg-emerald-900 text-emerald-300 border-emerald-700',
  data_analysis: 'bg-amber-900 text-amber-300 border-amber-700',
  fact_checking: 'bg-rose-900 text-rose-300 border-rose-700',
  text_synthesis: 'bg-violet-900 text-violet-300 border-violet-700',
}

const CAPABILITY_LABELS: Record<Capability, string> = {
  web_search: 'Web Search',
  code_generation: 'Code Gen',
  data_analysis: 'Data Analysis',
  fact_checking: 'Fact Check',
  text_synthesis: 'Text Synthesis',
}

function StatusIcon({ status }: { status: SubtaskStatus }) {
  switch (status) {
    case 'completed': return <CheckCircle2 size={16} className="text-emerald-400" />
    case 'failed': return <XCircle size={16} className="text-red-400" />
    case 'executing': return <Loader2 size={16} className="text-yellow-400 animate-spin" />
    case 'bidding': return <Zap size={16} className="text-violet-400 animate-pulse" />
    case 'assigned': return <Clock size={16} className="text-blue-400" />
    default: return <Circle size={16} className="text-gray-600" />
  }
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.8 ? 'text-emerald-400' : score >= 0.6 ? 'text-yellow-400' : 'text-red-400'
  return <span className={`text-xs font-mono font-bold ${color}`}>{pct}%</span>
}

interface Props {
  subtasks: Subtask[]
  winners: Record<string, Bid>
  activeSubtaskId: string | null
}

export function SubtaskList({ subtasks, winners, activeSubtaskId }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (subtasks.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-full">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Subtask DAG</h2>
        <p className="text-gray-600 text-sm">Waiting for task decomposition…</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Subtask DAG
        <span className="ml-2 text-xs text-gray-600 normal-case font-normal">
          {subtasks.filter(s => s.status === 'completed').length}/{subtasks.length} done
        </span>
      </h2>
      <div className="space-y-2 overflow-y-auto flex-1">
        {[...subtasks].sort((a, b) => a.order - b.order).map((subtask) => {
          const winner = winners[subtask.id]
          const isActive = subtask.id === activeSubtaskId
          const isExpanded = subtask.id === expandedId
          const hasResult = !!subtask.result

          return (
            <div
              key={subtask.id}
              className={`border rounded-lg transition-colors ${
                isActive
                  ? 'border-violet-600 bg-violet-950'
                  : subtask.status === 'completed'
                  ? 'border-gray-700 bg-gray-800/50'
                  : 'border-gray-800 bg-gray-800/30'
              }`}
            >
              <button
                className="w-full text-left p-3 cursor-pointer"
                onClick={() => setExpandedId(isExpanded ? null : subtask.id)}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 shrink-0">
                    <StatusIcon status={subtask.status} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 leading-snug">{subtask.description}</p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded border font-medium ${CAPABILITY_COLORS[subtask.required_capability]}`}>
                        {CAPABILITY_LABELS[subtask.required_capability]}
                      </span>
                      {subtask.dependency_ids.length > 0 && (
                        <span className="text-xs text-gray-600">
                          deps: {subtask.dependency_ids.join(', ')}
                        </span>
                      )}
                      {winner && (
                        <span className="text-xs text-gray-400">
                          → <span className="text-gray-300">{winner.agent_id.replace(/_/g, '-')}</span>
                        </span>
                      )}
                      {subtask.quality_score !== undefined && (
                        <ScoreBadge score={subtask.quality_score} />
                      )}
                    </div>
                  </div>
                  {hasResult && (
                    <div className="shrink-0 text-gray-600 mt-0.5">
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>
                  )}
                </div>
              </button>

              {isExpanded && subtask.result && (
                <div className="px-3 pb-3 pt-0 border-t border-gray-700/50 mt-1">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 font-semibold">Result preview</p>
                  <p className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                    {subtask.result}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
