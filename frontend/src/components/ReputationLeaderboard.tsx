import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { AgentProfile, Capability } from '../types'

interface RepChange {
  agentId: string
  capability: string
  delta: number
}

interface Props {
  agents: AgentProfile[]
  recentChanges: RepChange[]
}

const CAPABILITY_SHORT: Record<string, string> = {
  web_search: 'Web',
  code_generation: 'Code',
  data_analysis: 'Data',
  fact_checking: 'Fact',
  text_synthesis: 'Text',
}

function RepBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.75 ? 'bg-emerald-500' : value >= 0.55 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-800 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

export function ReputationLeaderboard({ agents, recentChanges }: Props) {
  if (agents.length === 0) return null

  const sorted = [...agents].sort((a, b) => {
    const avgA = Object.values(a.reputation).reduce((s, v) => s + v, 0) / (Object.values(a.reputation).length || 1)
    const avgB = Object.values(b.reputation).reduce((s, v) => s + v, 0) / (Object.values(b.reputation).length || 1)
    return avgB - avgA
  })

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Reputation Leaderboard
      </h2>
      <div className="space-y-4 overflow-y-auto flex-1">
        {sorted.map((agent, rank) => {
          const tierBadge = agent.tier === 'thorough'
            ? 'bg-violet-900 text-violet-300 border-violet-700'
            : 'bg-blue-900 text-blue-300 border-blue-700'
          const changes = recentChanges.filter(c => c.agentId === agent.id)

          return (
            <div key={agent.id} className="border border-gray-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 font-mono w-4">{rank + 1}</span>
                  <span className="text-sm font-medium text-gray-200">{agent.name}</span>
                </div>
                <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${tierBadge}`}>
                  {agent.tier}
                </span>
              </div>
              <div className="space-y-1.5">
                {Object.entries(agent.reputation).map(([cap, rep]) => {
                  const change = changes.find(c => c.capability === cap)
                  return (
                    <div key={cap}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs text-gray-500">{CAPABILITY_SHORT[cap] ?? cap}</span>
                        {change && (
                          <span className={`text-xs flex items-center gap-0.5 ${
                            change.delta > 0 ? 'text-emerald-400' : change.delta < 0 ? 'text-red-400' : 'text-gray-600'
                          }`}>
                            {change.delta > 0 ? <TrendingUp size={10} /> : change.delta < 0 ? <TrendingDown size={10} /> : <Minus size={10} />}
                            {Math.abs(change.delta * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                      <RepBar value={rep} />
                    </div>
                  )
                })}
              </div>
              <div className="flex gap-3 mt-2 text-xs text-gray-600">
                <span>✓ {agent.total_tasks_completed}</span>
                <span>✗ {agent.total_tasks_failed}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
