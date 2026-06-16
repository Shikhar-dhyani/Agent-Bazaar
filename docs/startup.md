# Agent Bazaar — Startup Guide

A complete walkthrough for getting Agent Bazaar running locally, understanding the system, and operating it in production.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Option A — Docker (Recommended)](#3-option-a--docker-recommended)
4. [Option B — Local Dev (No Docker)](#4-option-b--local-dev-no-docker)
5. [Verifying the Stack](#5-verifying-the-stack)
6. [System Architecture](#6-system-architecture)
7. [How the Pipeline Works](#7-how-the-pipeline-works)
8. [Agent Roster](#8-agent-roster)
9. [Auction & Reputation Mechanics](#9-auction--reputation-mechanics)
10. [WebSocket Event Reference](#10-websocket-event-reference)
11. [API Reference](#11-api-reference)
12. [Configuration Reference](#12-configuration-reference)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11 | Required for `match` syntax and `tomllib` |
| Node.js | 18 | Frontend dev server and build |
| Docker + Compose | Docker 24 / Compose v2 | For the Docker path only |
| Anthropic API key | — | All agents call the Claude API |

---

## 2. Environment Setup

Copy the example env file and fill in your API key:

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set:

```
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
REDIS_URL=redis://localhost:6379          # optional — omit to skip Redis
DATABASE_URL=postgresql+asyncpg://bazaar:bazaar@localhost:5432/agent_bazaar  # optional
```

> **Redis and Postgres are both optional.** The core auction loop runs entirely in-memory using `asyncio.Queue`. Only omit them if you don't need persistence across restarts.

---

## 3. Option A — Docker (Recommended)

This starts Redis, Postgres, the FastAPI backend, and the Vite frontend in one command.

```bash
# From the repo root
docker compose up --build
```

Services started:

| Service | Host port | What it is |
|---------|-----------|-----------|
| redis | 6379 | Event/session cache (optional) |
| postgres | 5432 | Task persistence (optional) |
| backend | 8000 | FastAPI + WebSocket server |
| frontend | 5173 | React dashboard (Vite dev) |

Open **http://localhost:5173** in your browser.

To stop:

```bash
docker compose down
# Wipe postgres volume too:
docker compose down -v
```

---

## 4. Option B — Local Dev (No Docker)

Run Redis and Postgres however you like (Homebrew, native, WSL), then start the backend and frontend separately.

### 4.1 Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install the package and all dependencies
pip install -e .

# Start the server with hot-reload
uvicorn agent_bazaar.api.main:app --reload --host 0.0.0.0 --port 8000
```

The server is ready when you see:

```
INFO:     Application startup complete.
```

### 4.2 Frontend

Open a second terminal:

```bash
cd frontend

npm install
npm run dev
```

The dashboard is available at **http://localhost:5173**.

> **Note:** The frontend reads `VITE_API_URL` (default `http://localhost:8000`) and `VITE_WS_URL` (default `ws://localhost:8000`). Override in a `frontend/.env` file if you deploy the backend elsewhere.

---

## 5. Verifying the Stack

Check these endpoints once the stack is running:

```bash
# Health — backend alive
curl http://localhost:8000/docs          # Swagger UI

# List registered agents
curl http://localhost:8000/api/agents

# Submit a test task (triggers the full pipeline)
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"request": "Explain the pros and cons of async/await in Python"}'
```

The POST returns immediately with a task object containing an `id`. Paste that ID into:

```bash
# Stream WebSocket events (requires wscat: npm i -g wscat)
wscat -c ws://localhost:8000/ws/<task_id>
```

You should see a stream of JSON events as the pipeline executes.

---

## 6. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser — React Dashboard (Vite + Tailwind)                │
│  TaskInput → [SubtaskList | BidStream | ReputationBoard]    │
│                        ResultPanel                          │
└────────────────────┬────────────────────────────────────────┘
                     │  HTTP POST /api/tasks
                     │  WebSocket /ws/{task_id}
┌────────────────────▼────────────────────────────────────────┐
│  FastAPI (uvicorn)                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ /api/tasks   │  │ /api/agents  │  │ /ws/{task_id}    │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
│         │ asyncio.create_task()        asyncio.Queue fan-out│
│  ┌──────▼──────────────────────────────────────────────┐    │
│  │  LangGraph StateGraph  (marketplace_graph)          │    │
│  │                                                     │    │
│  │  decompose → select_next ──→ collect_bids           │    │
│  │       ↑                          │                  │    │
│  │       │                    clear_auction            │    │
│  │       │                          │                  │    │
│  │  update_reputation ←── score ← execute              │    │
│  │       │                                             │    │
│  │       └──(all done)──→ aggregate → END              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Agents (Anthropic API)   Auction Engine   EMA Reputation   │
└─────────────────────────────────────────────────────────────┘
         │                              │
    Redis (optional)            Postgres (optional)
```

### Directory Layout

```
agent-bazaar/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── Dockerfile
│   └── src/agent_bazaar/
│       ├── config.py               # pydantic-settings (reads .env)
│       ├── models/
│       │   ├── task.py             # Task, TaskStatus
│       │   ├── subtask.py          # Subtask, Capability, SubtaskStatus
│       │   ├── bid.py              # Bid
│       │   └── agent_profile.py    # AgentProfile, AgentTier
│       ├── agents/
│       │   ├── broker.py           # Task → List[Subtask] via Claude Sonnet
│       │   ├── base_specialist.py  # bid() + execute() for all 10 agents
│       │   ├── scorer.py           # Quality score 0–1 via Claude Haiku
│       │   └── registry.py         # Mutable in-memory agent store
│       ├── auction/
│       │   ├── clearing.py         # Bid scoring + winner selection
│       │   └── reputation.py       # EMA reputation update
│       ├── graph/
│       │   ├── state.py            # MarketplaceState TypedDict
│       │   ├── nodes.py            # 8 async node functions
│       │   └── marketplace.py      # StateGraph compilation
│       ├── api/
│       │   ├── main.py             # FastAPI app + CORS
│       │   └── routes/
│       │       ├── tasks.py        # CRUD + _run_task background task
│       │       ├── agents.py       # GET /api/agents
│       │       └── websocket.py    # WebSocket stream endpoint
│       └── storage/
│           ├── redis_client.py     # Optional Redis helper
│           └── database.py         # Optional Postgres/SQLAlchemy
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── types.ts                # WSEvent discriminated union + all models
        ├── hooks/useWebSocket.ts   # WebSocket hook with stale-closure fix
        ├── App.tsx                 # Root — event dispatch, state, layout
        └── components/
            ├── TaskInput.tsx
            ├── SubtaskList.tsx
            ├── BidStream.tsx
            ├── ReputationLeaderboard.tsx
            └── ResultPanel.tsx
```

---

## 7. How the Pipeline Works

When you submit a task the following sequence runs as a background `asyncio` task:

### Step 1 — Decompose

`BrokerAgent` sends the raw request to **Claude Sonnet** with a structured prompt asking for 2–6 atomic subtasks. Each subtask has:

- A `required_capability` — one of: `web_search`, `code_generation`, `data_analysis`, `fact_checking`, `text_synthesis`
- `dependency_ids` — subtasks that must complete before this one can start
- An `order` integer for tie-breaking

The broker normalises LLM-returned IDs (which may come back as integers) to canonical `st_0`, `st_1`, … strings.

### Step 2 — Select Next Subtask

Finds all subtasks that are:
- Still in `PENDING` status, **and**
- Have all their `dependency_ids` in the `completed_subtask_ids` list

Picks the one with the lowest `order` value (i.e. respects DAG ordering). If none remain, routes to **Aggregate**.

### Step 3 — Collect Bids

All agents whose `capabilities` include the required capability submit a bid **in parallel** via `asyncio.gather`. Each agent calls its Claude model and returns:

```json
{
  "confidence": 0.85,
  "cost_multiplier": 1.2,
  "latency_multiplier": 0.9,
  "rationale": "Strong match for web search tasks"
}
```

Actual `estimated_cost = base_cost × cost_multiplier`, `estimated_latency = base_latency × latency_multiplier`.

### Step 4 — Clear Auction

The bid with the highest auction score wins:

```
score = 0.40 × confidence
      + 0.30 × (1 / (1 + estimated_cost / 10))
      + 0.30 × agent.reputation[capability]
```

Bids below `confidence < 0.3` are filtered out (fallback: all bids used if none qualify). Ties broken by lower estimated latency.

### Step 5 — Execute

The winning agent calls its Claude model with the subtask description and a context block containing the results of any dependency subtasks. Returns the full result text.

### Step 6 — Score

`ScorerAgent` (Claude Haiku) rates the result `0.0–1.0` and returns a short feedback string.

### Step 7 — Update Reputation

```
rep_new = 0.20 × quality_score + 0.80 × rep_old
```

Applied per-capability per-agent. `total_tasks_completed` increments if `quality_score >= 0.6`, otherwise `total_tasks_failed`.

Loop returns to **Select Next** until all subtasks are done.

### Step 8 — Aggregate

Claude Sonnet synthesises all subtask results into a single coherent final answer, which is stored on the `Task` object and streamed to the frontend.

---

## 8. Agent Roster

Ten pre-registered agents — two per capability (Fast = Haiku, Thorough = Sonnet):

| ID | Name | Tier | Model | Base Cost | Base Latency | Starting Rep |
|----|------|------|-------|-----------|--------------|-------------|
| `web_search_fast` | WebSearch-Fast | fast | Haiku | 2.0 | 3s | 0.60 |
| `web_search_thorough` | WebSearch-Thorough | thorough | Sonnet | 8.0 | 10s | 0.70 |
| `code_gen_fast` | CodeGen-Fast | fast | Haiku | 2.5 | 4s | 0.65 |
| `code_gen_thorough` | CodeGen-Thorough | thorough | Sonnet | 9.0 | 12s | 0.80 |
| `data_analysis_fast` | DataAnalysis-Fast | fast | Haiku | 2.0 | 3.5s | 0.60 |
| `data_analysis_thorough` | DataAnalysis-Thorough | thorough | Sonnet | 8.0 | 10s | 0.75 |
| `fact_check_fast` | FactCheck-Fast | fast | Haiku | 1.5 | 2.5s | 0.62 |
| `fact_check_thorough` | FactCheck-Thorough | thorough | Sonnet | 7.0 | 9s | 0.78 |
| `text_synthesis_fast` | TextSynthesis-Fast | fast | Haiku | 1.5 | 2s | 0.65 |
| `text_synthesis_thorough` | TextSynthesis-Thorough | thorough | Sonnet | 6.0 | 8s | 0.75 |

Reputation values are mutable at runtime — they shift with every completed subtask via EMA.

---

## 9. Auction & Reputation Mechanics

### Bid Scoring Formula

```
auction_score = 0.40 × confidence_score
              + 0.30 × cost_score
              + 0.30 × reputation[capability]

cost_score = 1.0 / (1.0 + estimated_cost / 10.0)
```

Higher confidence, lower cost, and higher reputation all improve a bid's score.

### Confidence Filter

Bids with `confidence_score < 0.3` are excluded from scoring. If *all* bids are below this threshold (e.g. every agent is uncertain), the filter is dropped and all bids compete.

### EMA Reputation Update

```
rep_new = α × quality_score + (1 − α) × rep_old      (α = 0.20)
```

An agent that consistently produces high-quality output sees its reputation drift toward 1.0 over time. A run of poor scores drags it toward 0.0. This causes the auction to self-organise: better agents win more often, earn better reputation, and win even more often.

### Reputation Convergence

| quality_score stream | rep converges toward |
|----------------------|---------------------|
| 1.0 every task | 1.0 |
| 0.5 every task | 0.5 (no change from default) |
| 0.0 every task | 0.0 |

---

## 10. WebSocket Event Reference

Connect to `ws://localhost:8000/ws/{task_id}`. On connect, all historical events are replayed, then live events stream until `task_completed` or `error`.

| `type` | Key fields | Triggered when |
|--------|-----------|----------------|
| `task_decomposed` | `subtasks[]` | Broker finishes splitting the task |
| `bid_submitted` | `subtask_id`, `bid` | Each agent submits a bid |
| `auction_cleared` | `subtask_id`, `winner`, `all_bids[]` | Auction winner is selected |
| `subtask_executing` | `subtask_id`, `agent_id`, `result_preview` | Agent starts executing |
| `subtask_scored` | `subtask_id`, `quality_score`, `feedback` | Scorer rates the output |
| `reputation_updated` | `agent_id`, `capability`, `old_reputation`, `new_reputation` | EMA update applied |
| `task_completed` | `final_answer` | Aggregation finishes |
| `error` | `message` | Unhandled exception in pipeline |
| `ping` | — | Keepalive (every 30s idle) |

---

## 11. API Reference

### `POST /api/tasks`

Submit a new task. Spawns the pipeline immediately in the background.

```json
// Request
{ "request": "Your complex multi-step task description" }

// Response (202-like, task starts in background)
{
  "id": "task_abc123",
  "raw_request": "...",
  "status": "pending",
  "created_at": "2026-06-16T10:00:00Z",
  "final_answer": null
}
```

### `GET /api/tasks`

List all in-memory tasks.

### `GET /api/tasks/{task_id}`

Get a single task by ID.

### `GET /api/tasks/{task_id}/subtasks`

List all subtasks for a task (with live status).

### `GET /api/tasks/{task_id}/bids`

Map of `subtask_id → [Bid, ...]` for all bids collected so far.

### `GET /api/tasks/{task_id}/events`

Full event history for a task (same as WebSocket replay).

### `GET /api/agents`

List all 10 registered agents with current reputation scores.

### `WebSocket /ws/{task_id}`

Stream events for a task. See [Section 10](#10-websocket-event-reference).

### Swagger UI

`http://localhost:8000/docs` — full interactive API explorer.

---

## 12. Configuration Reference

All config is read from `backend/.env` (or environment variables). Managed via `pydantic-settings`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | — | Anthropic API key — all agents use this |
| `REDIS_URL` | No | `None` | Redis connection string. If absent, Redis features are skipped |
| `DATABASE_URL` | No | `None` | Async Postgres DSN (`postgresql+asyncpg://...`). If absent, no DB persistence |

Frontend variables (set in `frontend/.env` or Docker Compose `environment:`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL for HTTP requests |
| `VITE_WS_URL` | `ws://localhost:8000` | Backend base URL for WebSocket |

---

## 13. Troubleshooting

### `ANTHROPIC_API_KEY not set` / `ValidationError`

The backend will refuse to start without a valid API key. Check that `backend/.env` exists and contains a valid `ANTHROPIC_API_KEY=sk-ant-...` line.

### `ModuleNotFoundError: No module named 'agent_bazaar'`

You need to install the package in editable mode first:

```bash
cd backend && pip install -e .
```

### Frontend shows blank / can't connect

1. Confirm the backend is running on port 8000: `curl http://localhost:8000/docs`
2. Check CORS — the backend allows `http://localhost:5173` and `http://localhost:3000` by default. If you're on a different port, add it in `backend/src/agent_bazaar/api/main.py`.
3. If running via Docker and hitting the frontend from a different machine, set `VITE_API_URL` to the host machine's IP.

### Task stuck in `bidding` / never reaches `executing`

All 10 agents bid concurrently. If the Anthropic API is rate-limited or a key is invalid, bids will fall back to default values (`confidence=0.5`). Watch the backend logs:

```bash
# Docker
docker compose logs -f backend

# Local
uvicorn agent_bazaar.api.main:app --reload --log-level debug
```

### Subtask dependency deadlock

If a subtask's `dependency_ids` reference IDs that don't exist, `select_next` will never find it ready and the pipeline will skip straight to `aggregate` with incomplete results. This can happen when re-using a stale `task_id` after a server restart (in-memory state is cleared on restart).

### Docker port conflicts

If ports 5173, 8000, 6379, or 5432 are already in use, either stop the conflicting process or change the host-side port in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"   # expose backend on 8001 instead
```

---

## Quick Reference Card

```bash
# Full stack (Docker)
docker compose up --build

# Backend only (local)
cd backend && pip install -e . && uvicorn agent_bazaar.api.main:app --reload

# Frontend only (local)
cd frontend && npm install && npm run dev

# Submit a task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"request": "Analyze and compare React vs Vue vs Svelte for a new project"}'

# Stream events for a task
wscat -c ws://localhost:8000/ws/<task_id>

# Check agent reputations
curl http://localhost:8000/api/agents | python -m json.tool
```
