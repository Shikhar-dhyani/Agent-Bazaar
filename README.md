# Agent Bazaar

A self-organizing multi-agent task marketplace where agents bid for work instead of being statically routed.

## How It Works

1. **Broker** decomposes an incoming task into a subtask DAG
2. **Specialists** self-assess confidence/cost/latency and submit bids
3. **Auction** clears — best weighted score (confidence + cost + reputation) wins
4. **Execute & Score** — winner runs the subtask, output is graded 0–1
5. **Reputation** updates via EMA per capability — the system learns which agents are reliable for which task types
6. Final results are aggregated into a coherent answer

## Agents

Two competing agents per capability (Haiku = fast/cheap, Sonnet = thorough/expensive):

| Capability       | Fast Agent             | Thorough Agent             |
|-----------------|------------------------|----------------------------|
| web_search      | WebSearch-Fast (Haiku) | WebSearch-Thorough (Sonnet)|
| code_generation | CodeGen-Fast (Haiku)   | CodeGen-Thorough (Sonnet)  |
| data_analysis   | DataAnalysis-Fast      | DataAnalysis-Thorough      |
| fact_checking   | FactCheck-Fast         | FactCheck-Thorough         |
| text_synthesis  | TextSynthesis-Fast     | TextSynthesis-Thorough     |

## Auction Formula

```
score = 0.40 × confidence + 0.30 × cost_score + 0.30 × reputation[capability]
```

Reputation updates via EMA after each scored execution:
```
rep_new = 0.20 × quality_score + 0.80 × rep_old
```

## Stack

- **Backend**: Python 3.11, FastAPI, LangGraph, Anthropic SDK, Redis, PostgreSQL
- **Frontend**: React + TypeScript + Vite + Tailwind CSS

## Quickstart

```bash
# 1. Set your Anthropic API key
cp backend/.env.example backend/.env
# Edit backend/.env and add ANTHROPIC_API_KEY

# 2. Start infrastructure
docker compose up redis postgres -d

# 3. Run backend
cd backend
pip install -e .
uvicorn agent_bazaar.api.main:app --reload

# 4. Run frontend
cd frontend
npm install
npm run dev
```

Or run everything with Docker:
```bash
ANTHROPIC_API_KEY=sk-... docker compose up
```

Then open http://localhost:5173
