# ContextLedger Lite

> Shared, searchable memory for AI agent teams — local, offline, no cloud required.

## The Problem

AI agents on dev teams start from zero every time. They re-discover the same bugs, re-derive the same solutions. Knowledge disappears between sessions. There's no institutional memory.

## The Solution

ContextLedger gives agents a **shared memory layer** backed by Actian VectorAI DB. Agents write structured memory entries (bug fixes, insights, solutions). Other agents retrieve relevant knowledge using **filtered vector search** — scoping by entry type, agent ID, or tag.

## Why Actian VectorAI DB

- **Filtered Search**: semantic meaning + structured filters (agent_id, entry_type, tags) — not just cosine similarity
- **Runs fully locally in Docker** — zero cloud dependency
- **Works fully offline** — local embeddings via sentence-transformers, no API calls
- Sub-15ms query latency, HNSW indexing

## Stack

| Component | Technology |
|---|---|
| Vector DB | Actian VectorAI DB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| API | FastAPI |
| Frontend | Vanilla JS |
| Client | Custom Python SDK (`contextledger`) |

---

## Setup & Run

### 1. Start Actian VectorAI DB
The database runs globally via Docker. Clone the official beta repository next to this project and start it:
```bash
git clone https://github.com/hackmamba-io/actian-vectorAI-db-beta.git
cd actian-vectorAI-db-beta
sudo docker compose up -d
```

### 2. Start the Backend API
Use a local virtual environment to install the Actian client `.whl` and start FastAPI:
```bash
cd contextledger
python3 -m venv .venv
source .venv/bin/activate
pip install "../actian-vectorAI-db-beta/actian_vectorai-0.1.0b2-py3-none-any.whl"
pip install fastapi uvicorn sentence-transformers python-dotenv pydantic httpx langchain grpcio protobuf numpy

cd backend
uvicorn main:app --reload
```
*(The API will be available at http://localhost:8000)*

### 3. Start the React Frontend
In a new terminal:
```bash
cd contextledger/frontend-react
npm install
npm run dev
```

### 4. Run the Agent Simulations
To demonstrate how AI agents securely interact with the memory ledger, run the simulation scripts in another terminal:
```bash
source .venv/bin/activate
python simulate_agents.py   # Simulates agent REST API interactions
python simulate_sdk.py      # Simulates native Python SDK integrations
```

---

## Project Structure

```
contextledger/
├── backend/
│   ├── main.py          # FastAPI — /memory, /search, /timeline, /stats
│   ├── memory.py        # Actian VectorAI SDK integrations
│   ├── embedder.py      # Local sentence-transformers wrapper
│   ├── models.py        # Pydantic schemas
│   └── agents/
│       ├── agent_debugger.py    
│       ├── agent_researcher.py  
│       └── agent_optimizer.py   
├── frontend-react/      # React + TS modern web UI (Vite)
├── sdk/
│   └── contextledger/   # Custom pip-installable Python SDK Client
├── simulate_agents.py   # Runs the 3 agents over HTTP REST
├── simulate_sdk.py      # Tests the native Python SDK
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/memory` | Store a memory entry |
| GET | `/search?q=...` | Semantic search + filtered retrieval |
| GET | `/timeline` | All entries, newest first |
| GET | `/stats` | Total memory count |

### Filtered Search Examples

```bash
# Semantic only
GET /search?q=how+to+fix+database+latency

# Filtered: only bug fixes
GET /search?q=memory+leak&entry_type=bug_fix

# Filtered: specific agent
GET /search?q=performance&agent_id=agent-optimizer

# Filtered: by tag
GET /search?q=embeddings&tag=hnsw
```

## Judging Criteria Alignment

| Criterion | How We Address It |
|---|---|
| VectorAI DB (30%) | Core storage + filtered search — not a wrapper |
| Real-world impact (25%) | Agents reusing knowledge = compounding intelligence |
| Technical execution (25%) | FastAPI + embeddings + simulation + clean architecture |
| Demo & presentation (20%) | Timeline UI + agent simulation script |
| **Bonus: local** | Runs 100% in Docker, no cloud |
| **Bonus: offline** | sentence-transformers local, zero API calls |