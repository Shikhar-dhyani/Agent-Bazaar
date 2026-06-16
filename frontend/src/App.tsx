import { useState, useEffect, useCallback } from 'react'
import type { Task, Subtask, Bid, AgentProfile, WSEvent } from './types'
import { TaskInput } from './components/TaskInput'
import { SubtaskList } from './components/SubtaskList'
import { BidStream } from './components/BidStream'
import { ReputationLeaderboard } from './components/ReputationLeaderboard'
import { ResultPanel } from './components/ResultPanel'
import { useWebSocket } from './hooks/useWebSocket'
import { Bot, Activity } from 'lucide-react'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface RepChange {
  agentId: string
  capability: string
  delta: number
}

function StatusPill({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: 'bg-gray-700 text-gray-300',
    decomposing: 'bg-violet-800 text-violet-200',
    bidding: 'bg-teal-800 text-teal-200',
    executing: 'bg-yellow-800 text-yellow-200',
    scoring: 'bg-orange-800 text-orange-200',
    completed: 'bg-emerald-800 text-emerald-200',
    failed: 'bg-red-800 text-red-200',
  }
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold uppercase tracking-wide ${colors[status] ?? 'bg-gray-700 text-gray-300'}`}>
      {status}
    </span>
  )
}

export default function App() {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [subtasks, setSubtasks] = useState<Subtask[]>([])
  const [bids, setBids] = useState<Record<string, Bid[]>>({})
  const [winners, setWinners] = useState<Record<string, Bid>>({})
  const [agents, setAgents] = useState<AgentProfile[]>([])
  const [repChanges, setRepChanges] = useState<RepChange[]>([])
  const [activeSubtaskId, setActiveSubtaskId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Fetch agents on mount and refresh periodically
  useEffect(() => {
    const fetchAgents = () =>
      fetch(`${API}/api/agents`)
        .then(r => r.json())
        .then(setAgents)
        .catch(() => {})

    fetchAgents()
    const id = setInterval(fetchAgents, 5000)
    return () => clearInterval(id)
  }, [])

  const handleWSEvent = useCallback((event: WSEvent) => {
    switch (event.type) {
      case 'task_decomposed':
        setSubtasks(event.subtasks)
        setTask(prev => prev ? { ...prev, status: 'decomposing' } : prev)
        break

      case 'bid_submitted':
        setActiveSubtaskId(event.subtask_id)
        setTask(prev => prev ? { ...prev, status: 'bidding' } : prev)
        setBids(prev => ({
          ...prev,
          [event.subtask_id]: [...(prev[event.subtask_id] ?? []), event.bid],
        }))
        break

      case 'auction_cleared':
        if (event.winner) {
          setWinners(prev => ({ ...prev, [event.subtask_id]: event.winner! }))
        }
        // Overwrite bids for this subtask with the scored versions from clearing
        setBids(prev => ({ ...prev, [event.subtask_id]: event.all_bids }))
        break

      case 'subtask_executing':
        setActiveSubtaskId(event.subtask_id)
        setTask(prev => prev ? { ...prev, status: 'executing' } : prev)
        setSubtasks(prev =>
          prev.map(s => s.id === event.subtask_id ? { ...s, status: 'executing' } : s)
        )
        break

      case 'subtask_scored':
        setTask(prev => prev ? { ...prev, status: 'scoring' } : prev)
        setSubtasks(prev =>
          prev.map(s =>
            s.id === event.subtask_id
              ? { ...s, quality_score: event.quality_score, status: 'completed' }
              : s
          )
        )
        break

      case 'reputation_updated':
        setRepChanges(prev => [
          { agentId: event.agent_id, capability: event.capability, delta: event.new_reputation - event.old_reputation },
          ...prev.slice(0, 19),
        ])
        setAgents(prev =>
          prev.map(a =>
            a.id === event.agent_id
              ? { ...a, reputation: { ...a.reputation, [event.capability]: event.new_reputation } }
              : a
          )
        )
        break

      case 'task_completed':
        setTask(prev => prev ? { ...prev, status: 'completed', final_answer: event.final_answer } : prev)
        setLoading(false)
        break

      case 'error':
        setTask(prev => prev ? { ...prev, status: 'failed' } : prev)
        setLoading(false)
        break
    }
  }, [])

  useWebSocket(activeTaskId, handleWSEvent)

  const handleSubmit = async (request: string) => {
    setLoading(true)
    setSubtasks([])
    setBids({})
    setWinners({})
    setActiveSubtaskId(null)
    setRepChanges([])

    try {
      const res = await fetch(`${API}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request }),
      })
      const newTask: Task = await res.json()
      setTask(newTask)
      setActiveTaskId(newTask.id)
    } catch {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot size={24} className="text-violet-400" />
          <div>
            <h1 className="text-lg font-bold text-gray-100">Agent Bazaar</h1>
            <p className="text-xs text-gray-500">Self-organizing multi-agent task marketplace</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {task && <StatusPill status={task.status} />}
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Activity size={12} className={loading ? 'text-emerald-400 animate-pulse' : 'text-gray-700'} />
            {agents.length} agents
          </div>
        </div>
      </header>

      <main className="p-6 space-y-4 max-w-screen-2xl mx-auto">
        {/* Task Input */}
        <TaskInput onSubmit={handleSubmit} loading={loading} />

        {/* Main Dashboard */}
        {(task || subtasks.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ minHeight: '500px' }}>
            <SubtaskList
              subtasks={subtasks}
              winners={winners}
              activeSubtaskId={activeSubtaskId}
            />
            <BidStream
              subtasks={subtasks}
              bids={bids}
              winners={winners}
            />
            <ReputationLeaderboard
              agents={agents}
              recentChanges={repChanges}
            />
          </div>
        )}

        {/* Final Answer */}
        {task?.final_answer && (
          <ResultPanel answer={task.final_answer} taskStatus={task.status} />
        )}
      </main>
    </div>
  )
}
