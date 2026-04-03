# Ralph Context Snapshot: HAB_Predictor MCP + Trajectory Artifact

## Task Statement
Implement an in-process STRATOS MCP wrapper that uses the full vendored
`LIFTS-UPRM/HAB_Predictor` Python codebase and renders a trajectory map artifact
in chat only when trajectory simulation tools run.

## Desired Outcome
- STRATOS backend calls HAB_Predictor Python functions directly with no separate
  ASTRA/HAB Flask server process.
- Simulation chat responses can include a map artifact with mean trajectory,
  launch/burst/landing markers, and one-sigma landing uncertainty.
- Non-trajectory chat responses remain text-only.

## Known Facts / Evidence
- `backend/mcp_servers/astra_server.py` currently wraps
  `vendor.astra_simulator_mcp`.
- `backend/llm.py` dispatches five `astra_*` tool names.
- Frontend messages currently carry text plus `toolCalls`, with no artifact field.
- HAB_Predictor `app.py` contains synchronous `get_balloon_catalog`,
  `get_parachute_catalog`, `calculate_nozzle_lift`, `calculate_balloon_volume`,
  and `run_simulation` functions.

## Constraints
- Use the full HAB_Predictor repo as the canonical vendor source, not only
  `astra/`.
- Do not run HAB_Predictor's Flask server as a sidecar.
- Preserve the current `astra_*` tool names and request schema.
- Add Leaflet/React-Leaflet for the trajectory artifact.
- Do not revert unrelated dirty worktree changes.

## Unknowns / Open Questions
- Whether existing backend tests cover enough ASTRA parity after wrapper swap.
- Whether frontend build requires dynamic import for Leaflet in Next.js.

## Likely Codebase Touchpoints
- `backend/vendor/hab_predictor/**`
- `backend/mcp_servers/astra_server.py`
- `backend/app/main.py`
- `backend/app/schemas.py`
- `backend/tests/test_llm_astra_tools.py`
- `frontend/src/types/chat.ts`
- `frontend/src/lib/chatApi.ts`
- `frontend/src/app/chat/page.tsx`
- `frontend/src/components/chat/MessageList.tsx`
- `frontend/src/components/chat/MessageList.module.css`
- `frontend/package.json`
