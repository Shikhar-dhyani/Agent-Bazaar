import { Trophy, Zap, DollarSign, Clock } from 'lucide-react'
import type { Bid, Subtask } from '../types'

interface AuctionRound {
  subtaskId: string
  subtaskDescription: string
  bids: Bid[]
  winnerId: string | null
}

interface Props {
  subtasks: Subtask[]
  bids: Record<string, Bid[]>
  winners: Record<string, Bid>
}

function BidRow({ bid, isWinner }: { bid: Bid; isWinner: boolean }) {
  const tierColor = bid.agent_id.includes('thorough')
    ? 'text-violet-400'
    : 'text-blue-400'

  return (
    <div className={`flex items-start gap-3 p-2.5 rounded-lg border text-sm transition-all ${
      isWinner
        ? 'border-amber-600 bg-amber-950/40'
        : 'border-gray-800 bg-gray-800/30'
    }`}>
      <div className="shrink-0 mt-0.5">
        {isWinner
          ? <Trophy size={14} className="text-amber-400" />
          : <Zap size={14} className={tierColor} />
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`font-medium ${isWinner ? 'text-amber-300' : 'text-gray-300'}`}>
            {bid.agent_id.replace(/_/g, '-')}
          </span>
          {isWinner && (
            <span className="text-xs bg-amber-800 text-amber-300 px-1.5 py-0.5 rounded font-semibold">
              WINNER
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5 truncate">{bid.rationale}</p>
        <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Zap size={11} />
            {(bid.confidence_score * 100).toFixed(0)}% conf
          </span>
          <span className="flex items-center gap-1">
            <DollarSign size={11} />
            {bid.estimated_cost.toFixed(1)}
          </span>
          <span className="flex items-center gap-1">
            <Clock size={11} />
            {bid.estimated_latency.toFixed(1)}s
          </span>
          {bid.auction_score !== undefined && (
            <span className="text-gray-500">
              score: <span className={isWinner ? 'text-amber-400 font-bold' : 'text-gray-400'}>
                {bid.auction_score.toFixed(3)}
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export function BidStream({ subtasks, bids, winners }: Props) {
  const rounds: AuctionRound[] = subtasks
    .filter(s => bids[s.id]?.length)
    .sort((a, b) => a.order - b.order)
    .map(s => ({
      subtaskId: s.id,
      subtaskDescription: s.description,
      bids: bids[s.id] ?? [],
      winnerId: winners[s.id]?.agent_id ?? null,
    }))

  if (rounds.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-full">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Live Auction</h2>
        <p className="text-gray-600 text-sm">Waiting for bids…</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Live Auction</h2>
      <div className="space-y-6 overflow-y-auto flex-1">
        {rounds.map(round => (
          <div key={round.subtaskId}>
            <p className="text-xs text-gray-500 mb-2 truncate" title={round.subtaskDescription}>
              <span className="text-gray-600 mr-1">[{round.subtaskId}]</span>
              {round.subtaskDescription}
            </p>
            <div className="space-y-1.5">
              {[...round.bids]
                .sort((a, b) => (b.auction_score ?? 0) - (a.auction_score ?? 0))
                .map(bid => (
                  <BidRow
                    key={bid.id}
                    bid={bid}
                    isWinner={bid.agent_id === round.winnerId}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
