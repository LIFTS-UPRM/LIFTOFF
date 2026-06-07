# STRATOS Hermes Multi-User Runtime

> **Status:** Proposed architecture for issue #115  
> **Primary goal:** Replace the centralized STRATOS chat-backend direction with a Hermes-style runtime: one separate agent instance per user, plus shared mission knowledge across the team.

---

## 1. Purpose

STRATOS should evolve into a mission operating system for LIFTS, not just a single chat API with mission tools attached.

The architecture target is:

- **one separate Hermes runtime per user**
- **one shared mission knowledge workspace per mission/project**
- **shared mission tools** usable by any user runtime
- **STRATOS orchestration** that connects identity, missions, docs, and tools

This document defines the first system shape strongly enough that implementation can begin without re-litigating core architectural decisions.

---

## 2. Problem statement

The current backend shape is useful for prototyping but is not the right long-term model.

Current traits in the repo:

- `backend/app/main.py` exposes a centralized `/chat` API
- `backend/app/schemas.py` uses a request model built around `message` + client-supplied `history`
- `backend/llm.py` contains a single shared provider contract, shared system prompt, and tool-group routing model
- the frontend currently posts chat requests as one central conversation stream (`frontend/src/lib/chatApi.ts`)

That model assumes STRATOS owns one main conversation runtime and users are just clients of that runtime.

That is not what LIFTS actually needs.

LIFTS needs:

- a separate mission copilot per member
- persistent user-level context per member
- shared mission knowledge across all members
- mission-level updates that can outlive any single user session

---

## 3. Core decision

### 3.1 Runtime decision

Each LIFTS member gets a **completely separate Hermes instance**.

"Separate" means:

- separate session history
- separate personal memory/context
- separate runtime-owned state
- potentially separate Hermes profile or equivalent isolated runtime identity

Users **do not** share:

- one agent process
- one conversation state
- one personal memory store
- one scratch workspace by default

### 3.2 Knowledge-sharing decision

Mission knowledge is shared through **Git-backed Markdown workspaces**.

Projects such as `AERO` and `SCRAM` should each have their own shared workspace.

Users share:

- mission docs
- procedures
- checklists
- status notes
- planning notes
- mission decisions
- references

This is the shared operational memory of the team.

### 3.3 STRATOS role decision

STRATOS should become the coordination layer that connects:

- user identity
- that user’s Hermes runtime
- the active mission workspace
- the mission tools available to that runtime
- approved writes back into shared mission knowledge

---

## 4. Design principles

1. **Agent isolation first**
   - Personal context belongs to the user runtime, not the shared mission layer.

2. **Mission knowledge is explicit and inspectable**
   - Shared knowledge should live in normal Markdown files, not hidden in opaque memory state.

3. **Git is the first synchronization mechanism**
   - v1 should optimize for visibility, reversibility, and low operational complexity.

4. **Tools are shared infrastructure, not shared memory**
   - Weather, trajectory, and airspace tools should be callable by any user runtime.

5. **Constrained writes before free-form autonomy**
   - In v1, STRATOS should allow narrow, auditable shared updates instead of arbitrary document rewrites.

6. **Mission-first scoping**
   - The first slice should solve pre-flight mission collaboration before tackling broad platform scope.

---

## 5. Architecture overview

The system has four layers.

### 5.1 Personal Hermes runtime layer

Each user gets a separate runtime instance.

That runtime owns:

- personal sessions
- personal context
- user preferences
- private drafts
- temporary working context
- personal memory not intended for mission-wide sharing

Examples:

- a user prefers concise answers
- a user has a private checklist draft
- a user asked a question earlier in the day and wants follow-up context

### 5.2 Shared mission workspace layer

Each mission/project gets a shared Markdown workspace.

Examples:

- `missions/aero/`
- `missions/scram/`

The workspace stores mission-global operational knowledge.

### 5.3 Mission tools layer

Mission tools remain common infrastructure.

Based on the current repo, these include:

- surface weather tools
- winds aloft tools
- SondeHub trajectory simulation
- no-flight-zone / airspace evaluation

These are shared capabilities any user runtime can call while working on a mission.

### 5.4 STRATOS coordination layer

STRATOS is responsible for:

- mapping app users to runtime identities
- selecting the active mission
- loading relevant shared mission docs
- exposing shared tools to the runtime
- handling controlled writes back to the shared mission workspace
- optionally tracking who changed what and when

---

## 6. Component diagram and system flow

### 6.1 Logical component diagram

```text
┌──────────────────────┐
│      Frontend UI     │
│ mission selection    │
│ chat / checklist UI  │
└──────────┬───────────┘
           │ HTTPS
           ▼
┌──────────────────────────────────────┐
│      STRATOS coordination layer      │
│ auth · routing · mission context     │
│ shared-doc loading · write gating    │
└───────┬──────────────────────┬───────┘
        │                      │
        │ invokes              │ reads/writes
        ▼                      ▼
┌───────────────────┐   ┌──────────────────────────┐
│ User Hermes       │   │ Shared mission workspace │
│ runtime (per user)│   │ Git-backed markdown      │
│ sessions/memory   │   │ missions/aero/...        │
└─────────┬─────────┘   └──────────────────────────┘
          │
          │ tool calls
          ▼
┌──────────────────────────────────────┐
│ Shared mission tool layer            │
│ weather · trajectory · airspace      │
│ SondeHub / ASTRA / NOTAM-style tools │
└──────────────────────────────────────┘
```

### 6.2 Component responsibilities

- **Frontend UI**
  - selects mission
  - renders chat, checklist, and mission outputs
  - sends user requests without being the source of trusted shared context

- **STRATOS coordination layer**
  - authenticates the user
  - resolves the user’s runtime identity
  - assembles shared mission context
  - validates and stages shared writes
  - acts as the trust boundary between client input and runtime input

- **User Hermes runtime**
  - owns personal session state
  - reasons over the user request plus shared mission context
  - calls mission tools
  - proposes structured shared updates

- **Shared mission workspace**
  - stores canonical team-readable mission knowledge
  - preserves history via Git
  - remains inspectable outside the runtime system

- **Shared mission tool layer**
  - provides mission data and calculations
  - remains reusable across user runtimes

### 6.3 High-level control flow

```text
User action
  -> Frontend submits request with mission_id
  -> STRATOS authenticates and resolves runtime
  -> STRATOS loads core + intent-specific mission docs
  -> STRATOS invokes the user’s Hermes runtime
  -> Runtime answers and may call shared mission tools
  -> Runtime returns response and optional structured write intent
  -> STRATOS applies/stages write if allowed
  -> Frontend renders final response and updated artifacts
```

---

## 7. Shared vs private boundary

This boundary is the most important rule in the system.

### 7.1 Private to the user runtime

Private data includes:

- user session history
- user preferences
- user-specific memory
- private drafts
- scratch notes
- unapproved work-in-progress
- transient reasoning state

This should not automatically become team-visible.

### 7.2 Shared at the mission layer

Shared data includes:

- official mission docs
- active mission status
- mission checklists
- procedures
- approved planning notes
- approved assumptions and constraints
- mission decisions and rationale
- reference material for all mission members

### 7.3 Rule of thumb

If the information should help **all mission members** operate better, it belongs in the shared mission workspace.

If the information is personal workflow state, draft reasoning, or user-local context, it belongs in the personal Hermes runtime.

---

## 8. Shared mission workspace structure

### 8.1 Root shape

```text
missions/
  aero/
    mission.md
    status/
      overview.md
      timeline.md
    checklists/
      preflight.md
      launch-day.md
      recovery.md
    procedures/
      communications.md
      launch-commit-criteria.md
    planning/
      trajectory-notes.md
      weather-notes.md
      launch-sites.md
    payload/
      payload-overview.md
    decisions.md
    references/
      contacts.md
      glossary.md

  scram/
    mission.md
    ...
```

### 8.2 Minimum required files for v1

Only require the smallest useful set:

```text
missions/
  <mission>/
    mission.md
    status/overview.md
    checklists/preflight.md
    planning/trajectory-notes.md
    planning/weather-notes.md
    decisions.md
```

This is enough for a first pre-flight copilot slice.

### 8.3 File intent

- `mission.md` — mission identity, purpose, constraints, top-level summary
- `status/overview.md` — current state, blockers, next milestone
- `checklists/preflight.md` — actionable operational checklist
- `planning/trajectory-notes.md` — trajectory findings and concerns
- `planning/weather-notes.md` — weather findings and concerns
- `decisions.md` — approved decisions and rationale

---

## 9. Runtime responsibilities

### 9.1 User runtime responsibilities

A user-level Hermes instance should:

- hold the user conversation state
- load user-local context
- receive the active mission selection
- request shared mission docs as needed
- call shared mission tools
- propose or execute constrained mission-doc updates

### 9.2 Mission workspace responsibilities

The mission workspace should:

- store canonical shared mission knowledge
- provide a stable file structure
- support diffable updates
- outlive any user session
- remain readable outside the agent system

### 9.3 STRATOS orchestration responsibilities

STRATOS should:

- authenticate the user
- resolve the user’s runtime identity
- determine the active mission
- select which shared mission files to load
- provide access to shared tools
- apply or stage approved writes
- maintain an audit trail where practical

---

## 10. Request flow for v1

### 10.1 Standard read/query flow

1. A user opens STRATOS.
2. The user selects a mission, for example `AERO`.
3. STRATOS routes the request to that user’s Hermes runtime.
4. STRATOS loads relevant shared mission documents for `AERO`.
5. The runtime receives:
   - the user message
   - the user’s personal session state
   - selected shared mission context
   - the shared mission tools
6. The runtime answers, optionally calling tools.

### 10.2 Shared update flow

1. The user asks to update shared mission knowledge.
2. STRATOS determines whether the requested write is allowed in v1.
3. The runtime prepares a constrained update.
4. STRATOS writes or stages the update into the mission workspace.
5. The change becomes visible to future users working on that mission.

---

## 11. v1 API contract

The backend contract should move from a client-owned chat-history payload to a STRATOS-owned mission-aware request.

### 11.1 Request shape

Suggested request body for the main v1 endpoint:

```json
{
  "user_id": "u_123",
  "mission_id": "aero",
  "session_id": "sess_abc123",
  "operation": "chat",
  "message": "What are the current pre-flight blockers?",
  "write_intent": null
}
```

Suggested fields:

- `user_id` — authenticated app user identity
- `mission_id` — active mission workspace
- `session_id` — runtime session handle returned by STRATOS/Hermes for continuity
- `operation` — request class such as `chat` or `write_intent`
- `message` — natural-language user request
- `write_intent` — optional structured write payload

### 11.2 Request rules

- the client may send user input and mission selection
- the client should not send trusted shared context as authoritative history
- STRATOS should resolve shared docs server-side
- Hermes should own conversation continuity and chat compaction internally, not the browser

### 11.3 Chat operation example

```json
{
  "user_id": "u_123",
  "mission_id": "aero",
  "session_id": "sess_abc123",
  "operation": "chat",
  "message": "Summarize the current AERO weather and trajectory concerns.",
  "write_intent": null
}
```

### 11.4 Structured write operation example

```json
{
  "user_id": "u_123",
  "mission_id": "aero",
  "session_id": "sess_abc123",
  "operation": "write_intent",
  "message": "Mark payload power verification complete.",
  "write_intent": {
    "operation": "checklist_item_set_status",
    "target_file": "missions/aero/checklists/preflight.md",
    "item_id": "payload-power-verification",
    "new_status": "done"
  }
}
```

### 11.5 Response shape

Suggested response body:

```json
{
  "response": "Current AERO blockers are launch-window wind uncertainty and payload power verification.",
  "source": "hermes-runtime",
  "session_id": "sess_abc123",
  "mission_id": "aero",
  "tool_calls": [
    {
      "name": "weather_summary",
      "args": {
        "mission_id": "aero"
      }
    }
  ],
  "trajectory_artifact": null,
  "write_result": null
}
```

### 11.6 Response fields

- `response` — final user-facing answer
- `source` — runtime/orchestrator source label
- `session_id` — runtime session returned for continuity
- `mission_id` — mission actually used for the request
- `tool_calls` — optional UI/debug metadata
- `trajectory_artifact` — optional map/trajectory payload
- `write_result` — optional outcome of a structured shared update

### 11.7 Write result example

```json
{
  "write_result": {
    "status": "applied",
    "operation": "checklist_item_set_status",
    "target_file": "missions/aero/checklists/preflight.md",
    "summary": "Marked payload power verification as complete."
  }
}
```

### 11.8 Endpoint recommendation for v1

Keep the first API surface small:

- `POST /runtime/request` — main mission-aware runtime endpoint
- optional later split into:
  - `POST /runtime/chat`
  - `POST /runtime/write`

A single endpoint is enough for the first vertical slice if `operation` is explicit.

---

## 12. Context loading strategy

v1 should avoid loading the entire mission workspace into every request.

### 12.1 Recommended approach

Use **mission-scoped selective loading**:

- always load a small core set
- load additional files based on request intent
- keep retrieval simple and deterministic in v1

### 12.2 Core files always loaded for v1

For an active mission, always load:

- `mission.md`
- `status/overview.md`
- `decisions.md`

### 12.3 Intent-based add-ons

Load additional files by request type:

- pre-flight task question → `checklists/preflight.md`
- weather question → `planning/weather-notes.md`
- trajectory question → `planning/trajectory-notes.md`
- launch procedure question → relevant file in `procedures/`

### 12.4 Why this approach

This keeps v1:

- understandable
- controllable
- cheap in context size
- easy to debug

A more advanced retrieval layer can come later.

### 12.5 Proposed context envelope for v1

To avoid ambiguity, STRATOS should assemble a runtime-owned context envelope before invoking a user Hermes runtime.

Suggested shape:

```json
{
  "user": {
    "user_id": "u_123",
    "display_name": "Armando"
  },
  "mission": {
    "mission_id": "aero",
    "title": "AERO"
  },
  "request": {
    "session_id": "sess_abc123",
    "message": "What are the current pre-flight blockers?",
    "operation": "chat",
    "write_intent": null
  },
  "shared_context": {
    "core_documents": [
      "missions/aero/mission.md",
      "missions/aero/status/overview.md",
      "missions/aero/decisions.md"
    ],
    "intent_documents": [
      "missions/aero/checklists/preflight.md"
    ]
  }
}
```

This makes the runtime boundary explicit:
- STRATOS owns mission selection and shared-doc assembly
- the user runtime owns reasoning and response generation
- the client does not get to define trusted mission context directly

---

## 13. Shared write policy

### 13.1 v1 principle

Do not allow unconstrained free-form agent rewriting of shared mission knowledge.

### 13.2 Allowed write categories in v1

Allow only constrained operations such as:

- append a planning note
- append a decision entry
- update mission status summary
- check/uncheck a checklist item
- add a dated note to trajectory or weather notes

### 13.3 Disallowed by default in v1

Disallow or gate:

- rewriting entire mission files
- broad folder restructuring
- deleting mission history
- editing arbitrary files outside the mission workspace
- cross-mission writes from the wrong mission context

### 13.4 Review model

Recommended v1 review policy:

- low-risk structured updates may auto-apply
- higher-risk updates should be staged for human confirmation

Examples:

- marking a checklist item complete → low risk
- rewriting `mission.md` top-level scope → requires review

### 13.5 Proposed write operation types for v1

To keep implementation narrow, shared writes should be represented as explicit operation types instead of arbitrary text-edit requests.

Suggested first operation set:

- `checklist_item_set_status`
- `append_planning_note`
- `append_decision_entry`
- `update_status_summary`

Suggested payload examples:

```json
{
  "operation": "checklist_item_set_status",
  "mission_id": "aero",
  "target_file": "missions/aero/checklists/preflight.md",
  "item_id": "payload-power-verification",
  "new_status": "done"
}
```

```json
{
  "operation": "append_planning_note",
  "mission_id": "aero",
  "target_file": "missions/aero/planning/weather-notes.md",
  "entry": {
    "author": "Armando",
    "timestamp": "2026-06-07T22:00:00Z",
    "content": "Surface winds are acceptable, but gusts near the launch window remain a caution item."
  }
}
```

This keeps the first implementation:
- testable
- auditable
- safe enough for team-shared files

---

## 14. Tool surface for v1

### 14.1 Include in v1

- shared mission doc read/load
- constrained shared mission doc write/update flow
- surface weather checks
- winds aloft checks
- trajectory simulation
- airspace/no-flight-zone checks
- concise mission copilot chat for pre-flight support

### 14.2 Exclude from v1

- live mission control orchestration
- full telemetry ingestion/runtime
- post-flight data pipeline design
- generalized SharePoint/document platform integration
- advanced permissioning/role systems
- large-scale autonomous knowledge refactoring

---

## 15. Mapping from current repo to target architecture

This section explains what happens to existing pieces.

### 15.1 `backend/app/main.py`

**Current role:** centralized chat API with request-level control.

**Future role:** either:

- a thin STRATOS orchestration entrypoint, or
- an adapter layer that forwards requests into user-scoped Hermes runtimes

It should stop being the architectural center of the conversation model.

### 15.2 `backend/app/schemas.py`

**Current role:** request/response contracts shaped around centralized chat.

**Future role:** evolve toward contracts that include:

- user/runtime identity
- mission identity
- shared-doc update intents

Client-supplied raw history should no longer be the main source of truth.

### 15.3 `backend/llm.py`

**Current role:** centralized provider abstraction, prompt, and tool grouping.

**Future role:** demote from system center to implementation detail.

The system should be organized around per-user Hermes runtimes first, not a single shared provider file first.

### 15.4 Current MCP-style mission tools

**Current role:** shared tool functions.

**Future role:** preserved as shared mission infrastructure.

These are still useful and should likely survive the migration.

### 15.5 Frontend chat flow

**Current role:** single API post with message + prior history.

**Future role:** mission-aware, user-runtime-aware request flow.

The frontend should conceptually talk to:

- a specific user runtime
- for a specific mission

not just a generic global chat backend.

### 15.6 Migration framing

The migration should happen in phases rather than as a single big-bang rewrite.

#### Phase 1 — keep useful infrastructure
Keep and reuse where possible:
- current mission tools
- map/trajectory artifact rendering
- existing frontend shell
- current mission list concepts

#### Phase 2 — change the request contract
Replace the current `message + history`-centric request shape with a contract centered on:
- authenticated user identity
- mission identity
- optional structured write intent

#### Phase 3 — add mission workspace loading
Add shared markdown mission loading before attempting advanced runtime changes.

This gives the system a real mission knowledge layer early.

#### Phase 4 — introduce per-user runtime isolation
Only after mission workspace loading is defined should STRATOS move fully to user-scoped Hermes runtimes.

This reduces the chance of mixing runtime redesign with knowledge-model redesign at the same time.

---

## 16. Identity and isolation model

### 16.1 User identity

STRATOS should maintain an application-level user identity.

That identity maps to:

- a Hermes runtime identity
- a personal session space
- a set of accessible missions

### 16.2 Mission identity

Each request should carry mission context explicitly.

At minimum:

- `mission_id`
- user identity
- requested operation type

### 16.3 Isolation guarantees

The system should guarantee:

- one user’s personal memory does not automatically become another user’s
- mission-shared writes are scoped to the active mission
- personal scratch work is not silently promoted to canonical mission knowledge

---

## 17. v1 vertical slice

The first proving slice should be narrowly defined.

### 17.1 Goal

A LIFTS member can open mission chat for `AERO`, ask a pre-flight planning question, get an answer grounded in shared mission docs and mission tools, and safely update approved shared mission notes.

### 17.2 Example scenarios

- “What are the current AERO pre-flight blockers?”
- “Summarize latest weather and trajectory concerns for AERO.”
- “Mark payload power verification complete in the AERO preflight checklist.”
- “Append today’s airspace concern to AERO planning notes.”

If these flows work cleanly, the architecture is validated.

---

## 18. Non-goals for this architecture phase

This document does **not** attempt to solve:

- full enterprise multi-tenant architecture
- long-term production auth/permissions design
- live mission control backend shape
- post-flight ingestion architecture
- advanced synchronization conflict resolution
- generalized knowledge graph / vector-memory platform work

Those can come after the pre-flight mission-copilot slice is proven.

---

## 19. Open questions intentionally left for follow-up issues

These should not block the architecture decision.

1. Should a user runtime map to a Hermes profile, a session namespace, or another isolation primitive?
2. Should shared mission docs live in the main STRATOS repo or a dedicated mission-docs repo?
3. What exact write operations should auto-apply vs require review?
4. What is the first audit-log format for mission doc changes?
5. What exact retrieval/loading mechanism should replace raw file loading later?

---

## 20. Follow-up implementation issues

Recommended order:

1. **[ARCH] Add mission workspace loader for shared markdown context**
2. **[BACKEND] Add per-user Hermes runtime/session abstraction**
3. **[BACKEND] Add mission-aware request contract (`user_id`, `mission_id`, `session_id`, `operation`)**
4. **[BACKEND] Add constrained shared mission doc write flow**
5. **[MVP] Build AERO pre-flight copilot vertical slice**

---

## 21. Acceptance criteria

This architecture is considered accepted when the team agrees that:

- STRATOS assumes **one separate Hermes runtime per user**
- mission knowledge is shared primarily through **Git-backed Markdown workspaces**
- the **private-vs-shared boundary** is explicit
- the **v1 request flow** is clear enough to implement
- the current centralized backend shape is clearly **demoted or replaced**
- the next implementation issues are obvious

---

## 22. Short version

STRATOS should be built as:

- **personal Hermes for each user**
- **shared mission Markdown for each mission**
- **shared mission tools for all users**
- **STRATOS orchestration that ties them together**

That is the correct architecture direction for LIFTS.