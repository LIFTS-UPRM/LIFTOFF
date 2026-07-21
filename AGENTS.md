# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What STRATOS Is

STRATOS is a high-altitude balloon (HAB) mission platform. It provides AI-assisted mission planning, live mission control, and postflight analysis. The primary working feature is a **Chat** module — an AI copilot backed by OpenAI that routes user messages to MCP tool servers for weather, airspace (NOTAM), and trajectory simulation (SondeHub Tawhiri).

## Repo Layout

```
backend/         FastAPI Python backend (Python 3.11, .venv311/)
  app/           Core app: main.py, config.py, schemas.py, prompt_assembly.py, logging.py, usage_log.py
  llm.py         OpenAI provider, tool schemas (WEATHER_TOOLS, AIRSPACE_TOOLS, SONDEHUB_TOOLS), tool dispatcher
  mcp_servers/   FastMCP tool servers: notam_server.py, sondehub_server.py, weather_server.py, astra_server.py
  vendor/        Vendored HAB predictor (BSD 3-Clause, excluded from lint/security scans)
  tests/         pytest tests
frontend/        Next.js 16 / React 19 / TypeScript frontend
  src/app/       page.tsx (login), layout.tsx, globals.css
  src/lib/       chatApi.ts (fetch wrapper), missions.ts
  src/types/     chat.ts, mission.ts
supabase/        Supabase config
docs/            PRD, SAD, TDD, DESIGN
```

## Commands

### Backend (from `backend/`)

```bash
# Use Python 3.11 venv
source ../.venv311/bin/activate   # or backend/.venv if it has packages

pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env              # fill in LLM_API_KEY and other secrets

uvicorn main:app --reload         # dev server at http://127.0.0.1:8000
ruff check .                      # lint (excludes vendor/)
pytest                            # run all tests
pytest tests/test_prompt_assembly.py   # run a single test file

# Security scan (same as CI)
bandit -r app mcp_servers main.py llm.py -x tests,vendor --severity-level medium --confidence-level medium
```

### Frontend (from `frontend/`)

```bash
npm install
npm run dev     # dev server at http://localhost:3000
npm run lint    # ESLint
npm run build   # production build (TypeScript check)
npm audit --audit-level=high   # security audit (same as CI)
```

### MCP servers (standalone, from `backend/`)

```bash
python -m mcp_servers.notam_server
python -m mcp_servers.weather_server
# sondehub_server runs in-process with FastAPI; standalone is optional
```

## Architecture: Chat Flow

The `/chat` POST endpoint is the core of the backend. The request lifecycle:

1. **Rate/size validation** — `_read_limited_body` + `_within_json_depth` guard before parsing.
2. **Intent routing** — `_select_relevant_tool_groups` keyword-matches the message against `TOOL_GROUP_INTENT_PATTERNS` to decide which tool schemas (weather/airspace/trajectory) to attach. Plain conversational turns send no tool schemas.
3. **Prompt assembly** — `prompt_assembly.py` wraps every piece of untrusted content (user message, history, tool output) in a JSON envelope with `"trust": "untrusted"`. Instruction-like strings are quarantined. This is the prompt injection defense layer.
4. **Tool-call loop** — up to 10 steps. `OpenAIProvider` (shared `AsyncOpenAI` client across requests) drives the loop. `execute_tool` dispatches to the relevant MCP server function.
5. **Trajectory artifact** — if `sondehub_run_simulation` or `get_balloon_no_flight_zone` returns a `trajectory_artifact`, it's parsed into `TrajectoryArtifact` and included in `ChatResponse` for the frontend map.

**Key file**: `backend/llm.py` holds all tool schemas (`WEATHER_TOOLS`, `AIRSPACE_TOOLS`, `SONDEHUB_TOOLS`), the `SYSTEM_PROMPT`, and the `execute_tool` dispatcher.

## Architecture: Tool Groups

Tool groups (`trajectory`, `weather`, `airspace`) control which OpenAI function schemas are sent per request. The intent router selects groups based on keyword matching so normal chat turns are fast (no tool schema payload). The frontend can also pass `enabled_tool_groups` in the request body to override. Tool continuation responses (e.g. "yes", "go ahead") look back at the last 6 history messages for intent.

## Prompt Security

All untrusted content (user input, history, tool output) is wrapped via `prompt_assembly.py` before reaching the model. Strings containing instruction-like patterns (`"ignore previous"`, `"you are now"`, `<system>`, etc.) are replaced with `"[quarantined]"`. Never bypass this wrapping when adding new message sources.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Key vars:

| Var | Purpose |
|-----|---------|
| `LLM_API_KEY` | OpenAI API key |
| `LLM_MODEL` | Model ID (default: `gpt-4o-mini`) |
| `FAA_CLIENT_ID` / `FAA_CLIENT_SECRET` | FAA NOTAM API credentials |
| `LAMINAR_USER_KEY` | Laminar observability |
| `SONDEHUB_TAWHIRI_ENDPOINT` | SondeHub trajectory API |

Frontend uses `NEXT_PUBLIC_BACKEND_URL` (defaults to `http://127.0.0.1:8000` on localhost).

## PR / CI Requirements

All changes to `main` go through PRs. Three CI workflows must pass:
- **Frontend CI**: `npm ci` → lint → build
- **Backend CI**: pip install → `ruff check .` → `python -c "import main"` → `pytest`
- **Security CI**: bandit (backend) + `npm audit` (frontend)

Branch naming: `feature/<name>`, `fix/<name>`, `chore/<name>`.

## Vendored Code

`backend/vendor/hab_predictor/` is the legacy ASTRA HAB predictor (BSD 3-Clause). It is excluded from ruff lint (`ruff.toml`) and bandit scans. Do not modify vendored code — STRATOS uses SondeHub Tawhiri for all trajectory prediction; ASTRA is retained for reference only.
