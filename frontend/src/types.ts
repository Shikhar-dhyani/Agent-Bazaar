export type TaskStatus =
  | 'pending' | 'decomposing' | 'bidding'
  | 'executing' | 'scoring' | 'completed' | 'failed'

export type SubtaskStatus =
  | 'pending' | 'bidding' | 'assigned' | 'executing' | 'completed' | 'failed'

export type AgentTier = 'fast' | 'thorough'
export type Capability =
  | 'web_search' | 'code_generation' | 'data_analysis' | 'fact_checking' | 'text_synthesis'

export interface Task {
  id: string
  raw_request: string
  status: TaskStatus
  final_answer?: string
  created_at: string
  completed_at?: string
}

export interface Subtask {
  id: string
  parent_task_id: string
  description: string
  required_capability: Capability
  dependency_ids: string[]
  status: SubtaskStatus
  result?: string
  assigned_agent_id?: string
  quality_score?: number
  order: number
}

export interface Bid {
  id: string
  subtask_id: string
  agent_id: string
  confidence_score: number
  estimated_cost: number
  estimated_latency: number
  rationale: string
  auction_score?: number
  created_at: string
}

export interface AgentProfile {
  id: string
  name: string
  tier: AgentTier
  capabilities: Capability[]
  reputation: Record<string, number>
  base_cost: number
  base_latency: number
  model: string
  total_tasks_completed: number
  total_tasks_failed: number
}

export type WSEvent =
  | { type: 'task_decomposed'; task_id: string; subtasks: Subtask[] }
  | { type: 'bid_submitted'; task_id: string; subtask_id: string; bid: Bid }
  | { type: 'auction_cleared'; task_id: string; subtask_id: string; winner: Bid | null; all_bids: Bid[] }
  | { type: 'subtask_executing'; task_id: string; subtask_id: string; agent_id: string; result_preview: string }
  | { type: 'subtask_scored'; task_id: string; subtask_id: string; quality_score: number; feedback: string }
  | { type: 'subtask_failed'; task_id: string; subtask_id: string; reason: string }
  | { type: 'reputation_updated'; task_id: string; agent_id: string; capability: string; old_reputation: number; new_reputation: number; quality_score: number }
  | { type: 'task_completed'; task_id: string; final_answer: string }
  | { type: 'error'; task_id: string; message: string }
  | { type: 'ping' }
