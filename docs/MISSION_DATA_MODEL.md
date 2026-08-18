# Mission Data Model

**Status**: Core specification for STRATOS platform  
**Last Updated**: 2026-07-22  
**Audience**: Backend (schema, API), Frontend (chat, dashboard, analysis), Data pipeline

---

## Overview

The Mission Data Model defines how STRATOS represents high-altitude balloon (HAB) missions, from pre-flight planning through postflight analysis. It supports:

- **Multi-user chat** (copilot with mission context)
- **Real-time telemetry dashboard** ("In Flight" view)
- **Mission control** (launch approval, flight tracking)
- **Postflight analysis** (recovery data, scientific results)

All untrusted data (user input, tool output, chat history) flows through `prompt_assembly.py` wrapping before reaching the LLM.

---

## Core Entities

### MISSION

A campaign with one or more launch attempts. Represents a scientific or operational objective at LIFTS.

```
id: UUID
name: string (e.g., "ASCENT")
description: string
state: Planning | Ready | Active | Complete
team: [TeamMember]
flights: [Flight]
skills: [Skill]

created_by: User
created_at: timestamp
updated_by: User
updated_at: timestamp
```

**State Transitions:**
- `Planning` → `Ready` (all preflight complete, teams ready)
- `Ready` → `Active` (Flight launched)
- `Active` → `Complete` (all Flights recovered/analyzed)

### FLIGHT

One balloon launch attempt. Same Mission may have multiple Flights (abort/retry scenario).

```
id: UUID
mission_id: UUID → Mission
launch_date_planned: datetime
launch_window: string (e.g., "06:00-08:00 AST")

state: Preparing | Armed | Launched | In Flight | Recovered | Analyzed
payload_id: UUID → Payload

telemetry_stream: WebSocket endpoint
  └─ live sensor data (ephemeral, for "In Flight" dashboard only)

tool_calls: [ToolCall]
approval: Approval
recovery_status: not_attempted | in_progress | recovered | lost
recovery_location: {lat, lon} (if recovered)

created_by: User
created_at: timestamp
updated_by: User
updated_at: timestamp
```

**State Transitions:**
- `Preparing` → `Armed` (preflight checks complete, ready to launch)
- `Armed` → `Launched` (balloon released)
- `Launched` → `In Flight` (ascending, transmitting telemetry)
- `In Flight` → `Recovered` (payload found, mission concluded)
- `Recovered` → `Analyzed` (data processed, report written)

### PAYLOAD

The physical balloon + gondola + instruments. One per Flight.

```
id: UUID
flight_id: UUID → Flight
name: string
mass_kg: float
dimensions: string (e.g., "30cm × 20cm × 15cm")
sub_missions: [SubMission]
```

### SUB_MISSION

A scientific objective bundled in one Payload. Example: ASCENT mission has SCRAM (solar cells) + AERO (ozone detection).

```
id: UUID
payload_id: UUID → Payload
name: string (e.g., "SCRAM", "AERO")
scientific_objective: string
instruments: [Instrument]
success_criteria: string
```

### INSTRUMENT

A sensor or device on the Payload.

```
id: UUID
sub_mission_id: UUID → SubMission
name: string
type: string (e.g., "temperature sensor", "UV spectrometer", "GPS")
vendor: string
quantity: int
power_draw_mA: float
```

### TEAM_MEMBER

User role/permissions within a Mission.

```
id: UUID
user_id: UUID → User
mission_id: UUID → Mission
role: Captain | Co-Captain | Chief_Engineer | Team_Member | Observer
auth_level: full_control | edit | view_only

created_at: timestamp
created_by: User
```

### TOOL_CALL

Decision artifact from copilot tool execution (weather, trajectory, airspace). Stores *rationale only*, not raw tool output.

```
id: UUID
flight_id: UUID → Flight
tool: weather | trajectory | airspace
decision_rationale: string
  └─ e.g., "chose 06:00 launch window; forecast shows clear conditions and optimal winds"
initiated_by: User
timestamp: datetime
```

### APPROVAL

Launch approval record. Gate decision by Captain/Co-Captain/Chief Engineers.

```
id: UUID
flight_id: UUID → Flight
approved_by: [User] (roles: Captain, Co-Captain, Chief_Engineer)
approved_at: datetime
basis_report: string (summary of readiness, resources, risks)
external_notification_sent: bool
```

### SKILL

Reusable workflow or checklist template for mission operations.

```
id: UUID
mission_id: UUID → Mission
type: interactive_workflow | checklist_template
name: string (e.g., "Pre-Launch Payload Checklist", "Launch Readiness Review")
description: string

if interactive_workflow:
  steps: [
    {
      order: int,
      prompt: string (copilot asks user),
      expected_input: string,
      on_response: function (copilot behavior)
    }
  ]

if checklist_template:
  fields: [
    {
      name: string,
      type: text | number | checkbox | select,
      required: bool,
      validation: regex | range | enum
    }
  ]

created_by: User
created_at: timestamp
```

---

## Data Flows

### Pre-Flight Planning

1. User creates Mission in chat or UI
2. Team members collaborate via chat (copilot context aware)
3. Copilot calls weather/trajectory/airspace tools → stores decision rationale on Flight
4. Skills (interactive workflows or checklists) executed during planning
5. Approval gate: Captain/Co-Captain/Chief Engineers review basis_report → approve or reject

### Launch & In-Flight

1. Flight state: `Armed` → `Launched`
2. Telemetry stream opens (WebSocket)
3. "In Flight" dashboard consumes telemetry (ephemeral, ephemeral only)
4. Chat remains available for live questions/tool calls (e.g., "should we adjust recovery window?")
5. Tool calls during flight stored as decision artifacts

### Recovery & Analysis

1. Payload recovered; state: `In Flight` → `Recovered`
2. Real telemetry data (from recovered device) uploaded separately (outside STRATOS)
3. Mission state: `Recovered` → `Analyzed`
4. Postflight chat/analysis tools query recovered data (not live WebSocket)

---

## Access Patterns

### Chat Endpoint

**Input**: User message, Mission ID (selected), Flight ID (if active)  
**Output**: Copilot response (possibly calling tools)

Queries:
- `Mission.flights` (to show active/recent flights)
- `Flight.tool_calls` (context for continuation, e.g., "go ahead with that launch window")
- `Mission.team` (who can chat about this mission)

### In-Flight Dashboard

**Input**: Flight ID (active)  
**Output**: Live telemetry stream via WebSocket

Queries:
- `Flight.telemetry_stream` (WebSocket connection)
- `Flight.state`, `Flight.recovery_status`
- `Payload.sub_missions`, `Payload.instruments` (static, for UI labels)

### Postflight Analysis

**Input**: Flight ID (recovered)  
**Output**: Analysis UI (charts, reports)

Queries:
- `Flight.state` (must be `Analyzed`)
- `Flight.tool_calls` (decisions made during flight)
- `Flight.approval` (authorization trail)
- External telemetry service (real data from recovered payload)

---

## Audit Trail

Every entity records:
- `created_by`, `created_at`
- `updated_by`, `updated_at` (on state changes)
- `TOOL_CALL.initiated_by` (who triggered tool)
- `TEAM_MEMBER.created_by` (who added this member)
- `APPROVAL` (full approval chain)

Purpose: Accountability, postflight review, compliance.

---

## Schema Notes

- **Telemetry**: Live stream is ephemeral (WebSocket ephemeral); real data from payload recovery stored externally
- **Tool output**: Only rationale stored; raw API responses discarded after decision made
- **Multi-user**: Private chat threads per Mission; shared knowledge base from all conversations; roles control approval/editing
- **State immutability**: Once `Recovered`, Flight.state can only transition to `Analyzed`; launch_date_planned is locked after `Launched`

---

## Next: Schema Validation

This model unblocks:
1. **Backend schema** (database tables, FastAPI models in `schemas.py`)
2. **API endpoints** (chat, mission CRUD, flight creation, telemetry WebSocket)
3. **Frontend architecture** (chat layout, dashboard, analysis UI structure)

Ready for database schema review?
