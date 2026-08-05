# AI Engineering Lab

Platform for building, analyzing, and improving production AI systems.

The first module is **Architecture Critic** — engineered feedback on AI system architectures, in the spirit of a Staff AI Engineer. This repository currently establishes the project foundation only; AI analysis is intentionally not implemented yet.

## Repository structure

```
AI Engineering Labs/
├── frontend/          # Next.js (App Router) + TypeScript + Tailwind + shadcn/ui
├── backend/           # FastAPI + Python 3.12
└── README.md
```

---

## Frontend (`frontend/`)

| Folder | Purpose |
|--------|---------|
| `app/` | Next.js App Router — routes, layouts, and page-level composition |
| `components/` | Reusable React components (`ui/` for shadcn primitives; feature folders such as `landing/` for page-specific UI) |
| `lib/` | Shared utilities and configuration (class merging, API base URL, app constants) |
| `services/` | HTTP/API client layer — isolatates backend calls from UI components |
| `types/` | Shared TypeScript contracts aligned with backend schemas |
| `public/` | Static assets served by Next.js |

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Backend (`backend/`)

| Folder | Purpose |
|--------|---------|
| `app/api/` | HTTP layer — FastAPI routers and endpoint handlers (thin controllers) |
| `app/core/` | Cross-cutting infrastructure: settings, environment configuration |
| `app/models/` | Domain / persistence models (reserved for database entities) |
| `app/schemas/` | Pydantic request/response DTOs — the public API contract |
| `app/services/` | Business logic orchestration; keeps routers free of domain rules |
| `app/reviewers/` | Pluggable architecture review engines (e.g. future Architecture Critic) |
| `app/prompts/` | Versioned prompt templates for future LLM calls |
| `app/utils/` | Pure shared helpers with no business logic |
| `app/main.py` | Application factory, middleware, and router mounting |

### Run the backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health) → `{ "status": "ok" }`

---

## Architecture decisions

### Monorepo with clear frontend / backend boundary
A single repository keeps the lab modules co-located while allowing each side to evolve its own toolchain (npm vs pip). Shared contracts can later move into a dedicated package if needed.

### Clean layered backend
```
Request → api (router) → services → reviewers / models
                ↓
             schemas (DTO boundary)
```
- **Routers** only parse HTTP and call services.
- **Services** own orchestration and use cases.
- **Reviewers** are strategy objects for analysis — new critics can be added without changing the HTTP surface.
- **Schemas** are the serialization boundary; **models** are reserved for persistence when it arrives.
- **Prompts** stay outside service code so prompt iteration does not require touching business logic.

### Frontend separation of concerns
- **Pages** compose UI; they do not talk to the network directly.
- **Services** own `fetch` / API details.
- **Types** mirror backend schemas to keep the contract explicit.
- **shadcn/ui** under `components/ui/` provides accessible primitives without locking the design system into a heavy component library.

### No AI dependencies yet
LangChain, vector databases, and authentication are deliberately omitted. The structure leaves clear extension points (`reviewers/`, `prompts/`, `services/`) for when analysis is introduced.

### CORS for local development
The API allows `localhost:3000` so the Next.js app can call the backend during development without ad-hoc proxy hacks. Origins remain configurable via settings.

### Health endpoint first
`GET /health` is the baseline operational signal for local smoke tests, containers, and future load balancers.

---

## Current scope

| Included | Not included (yet) |
|----------|--------------------|
| Project scaffolding | LLM / AI reasoning |
| Architecture review workflow | LangChain / LLM SDKs |
| Deterministic Scalability + Observability reviewers | Vector databases |
| `POST /review` + health endpoint | Authentication |
| Split form / report UI | Non-deterministic feedback |

---

## Module roadmap (non-binding)

1. **Foundation** ← you are here
2. Architecture Critic input / review API
3. Structured feedback UI
4. Additional lab modules
