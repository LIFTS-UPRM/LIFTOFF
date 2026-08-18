# API Specification

**Status**: Core specification for STRATOS backend  
**Last Updated**: 2026-07-22  
**Audience**: Frontend (Next.js), Backend (FastAPI), Backend-to-backend integrations (MCP servers)

---

## Overview

STRATOS provides a RESTful API for mission management, flight operations, and AI-assisted planning. All requests require JWT authentication. The API serves:

- **Frontend** (Next.js): Mission chat, flight dashboard, team management
- **Backend integrations**: MCP tool servers, external telemetry systems

Response format is JSON. Streaming telemetry uses WebSocket.

---

## Authentication

### JWT Flow

1. User logs in with credentials → `/auth/login`
2. Backend returns `access_token` (JWT) and optional `refresh_token`
3. Client includes token in Authorization header: `Authorization: Bearer <access_token>`
4. Token expires; client refreshes via `/auth/refresh`

**JWT Payload** (example):
```json
{
  "sub": "user_id",
  "email": "user@uprm.edu",
  "roles": ["Captain"],
  "exp": 1700000000
}
```

### Token Expiry

- `access_token`: 1 hour
- `refresh_token`: 7 days (optional, for long-lived sessions)

---

## Base URL & Format

**Development**: `http://127.0.0.1:8000`  
**Production**: `https://api.stratos.lifts.uprm.edu` (or deployed domain)

**Response Format**: JSON with consistent structure:

```json
{
  "success": true,
  "data": { /* entity or list */ },
  "error": null,
  "timestamp": "2026-07-22T13:00:00Z"
}
```

**Error Response**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FLIGHT_NOT_FOUND",
    "message": "Flight with ID xyz not found",
    "status": 404
  },
  "timestamp": "2026-07-22T13:00:00Z"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PUT) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (e.g., state transition invalid) |
| 500 | Server Error |

---

## Query Parameters

### Pagination

Use `limit` and `offset` (or `cursor` for keyset pagination):

```
GET /missions?limit=10&offset=20
GET /missions?limit=10&cursor=eyJpZCI6ICIxMjMifQ==
```

**Default**: `limit=20`, `offset=0`

### Filtering

```
GET /missions?state=Ready&created_by={user_id}
GET /flights?mission_id={mission_id}&state=In%20Flight
```

Supported filters per endpoint listed below.

### Sorting

```
GET /missions?order_by=created_at%20desc
GET /flights?order_by=launch_date_planned%20asc
```

### Field Selection

```
GET /missions/123?fields=id,name,state,created_at
```

Returns only specified fields. Default returns all fields.

---

## Endpoints

### Authentication

#### POST `/auth/login`

**Request**:
```json
{
  "email": "user@uprm.edu",
  "password": "password123"
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "user": {
      "id": "user_123",
      "email": "user@uprm.edu",
      "roles": ["Captain"],
      "name": "John Doe"
    }
  }
}
```

#### POST `/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "expires_in": 3600
  }
}
```

---

### Missions

#### GET `/missions`

List missions (paginated, filterable).

**Query Params**:
- `limit`, `offset`: pagination
- `state`: Planning | Ready | Active | Complete
- `created_by`: user_id
- `order_by`: created_at, name, state
- `fields`: id,name,state,team,flights

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "mission_001",
      "name": "ASCENT",
      "state": "Ready",
      "description": "Solar cells and ozone research",
      "created_by": "user_123",
      "created_at": "2026-06-01T10:00:00Z",
      "team": [
        {"user_id": "user_123", "role": "Captain"},
        {"user_id": "user_456", "role": "Chief_Engineer"}
      ],
      "flights": ["flight_001", "flight_002"]
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 5
  }
}
```

#### POST `/missions`

Create a new mission.

**Request**:
```json
{
  "name": "ASCENT",
  "description": "Solar cells and ozone research",
  "team": [
    {"user_id": "user_123", "role": "Captain"},
    {"user_id": "user_456", "role": "Team_Member"}
  ]
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "id": "mission_001",
    "name": "ASCENT",
    "state": "Planning",
    "created_by": "user_123",
    "created_at": "2026-07-22T13:00:00Z"
  }
}
```

#### GET `/missions/{id}`

Fetch a mission by ID.

**Response** (200): Full mission entity (as above).

#### PUT `/missions/{id}`

Update mission (name, description, team membership).

**Request**:
```json
{
  "name": "ASCENT v2",
  "state": "Ready"
}
```

**Response** (200): Updated mission entity.

#### DELETE `/missions/{id}`

Delete a mission (only if state=Planning; otherwise 409 Conflict).

**Response** (204): No content.

---

### Flights

#### GET `/missions/{mission_id}/flights`

List flights for a mission.

**Query Params**:
- `state`: Preparing | Armed | Launched | In%20Flight | Recovered | Analyzed
- `order_by`: launch_date_planned, created_at

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "flight_001",
      "mission_id": "mission_001",
      "launch_date_planned": "2026-07-28T06:00:00Z",
      "launch_window": "06:00-08:00 AST",
      "state": "Armed",
      "payload_id": "payload_001",
      "recovery_status": "not_attempted",
      "created_at": "2026-07-22T13:00:00Z",
      "created_by": "user_123"
    }
  ]
}
```

#### POST `/missions/{mission_id}/flights`

Create a new flight for a mission.

**Request**:
```json
{
  "launch_date_planned": "2026-07-28T06:00:00Z",
  "launch_window": "06:00-08:00 AST",
  "payload_id": "payload_001"
}
```

**Response** (201): Flight entity with state=Preparing.

#### GET `/flights/{id}`

Fetch a flight by ID.

**Response** (200): Full flight entity.

#### PUT `/flights/{id}`

Update flight (launch window, recovery plan, state transitions).

**Request**:
```json
{
  "state": "Armed",
  "launch_window": "07:00-09:00 AST"
}
```

**Response** (200): Updated flight entity.

**State Transition Validation**:
- Preparing → Armed (OK)
- Armed → Launched (OK)
- Launched → In Flight (OK)
- In Flight → Recovered (OK)
- Recovered → Analyzed (OK)
- Any backward transition → 409 Conflict

#### DELETE `/flights/{id}`

Delete a flight (only if state=Preparing; otherwise 409 Conflict).

**Response** (204): No content.

---

### Payloads

#### POST `/flights/{flight_id}/payloads`

Create a payload for a flight.

**Request**:
```json
{
  "name": "ASCENT Gondola",
  "mass_kg": 2.3,
  "dimensions": "30cm x 20cm x 15cm",
  "sub_missions": [
    {"name": "SCRAM", "scientific_objective": "Solar cell efficiency at altitude"},
    {"name": "AERO", "scientific_objective": "Ozone layer analysis"}
  ]
}
```

**Response** (201): Payload entity with sub_missions and instruments.

#### GET `/payloads/{id}`

Fetch a payload by ID (includes sub_missions and instruments).

**Response** (200): Full payload entity.

#### PUT `/payloads/{id}`

Update payload metadata (name, mass, dimensions). Cannot modify sub_missions once flight is Launched.

**Response** (200): Updated payload entity.

#### DELETE `/payloads/{id}`

Delete a payload (only if flight state=Preparing).

**Response** (204): No content.

---

### Team Management

#### GET `/missions/{id}/team`

List team members for a mission.

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "member_001",
      "user_id": "user_123",
      "mission_id": "mission_001",
      "role": "Captain",
      "auth_level": "full_control",
      "created_at": "2026-07-22T13:00:00Z"
    }
  ]
}
```

#### POST `/missions/{id}/team`

Add a team member to a mission.

**Request**:
```json
{
  "user_id": "user_456",
  "role": "Chief_Engineer",
  "auth_level": "edit"
}
```

**Response** (201): Team member entity.

#### PUT `/missions/{mission_id}/team/{member_id}`

Update team member role/auth level.

**Request**:
```json
{
  "role": "Co_Captain",
  "auth_level": "full_control"
}
```

**Response** (200): Updated member entity.

#### DELETE `/missions/{mission_id}/team/{member_id}`

Remove team member from mission.

**Response** (204): No content.

---

### Chat

#### POST `/missions/{id}/chat`

Send a message to the AI copilot for a mission context.

**Request**:
```json
{
  "message": "What's the weather forecast for launch day?",
  "flight_id": "flight_001",
  "enabled_tool_groups": ["weather", "trajectory"]
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "response": "Based on the forecast for 2026-07-28...",
    "tool_calls": [
      {
        "id": "tool_call_123",
        "tool": "weather",
        "decision_rationale": "chose 06:00 launch window; forecast shows clear conditions"
      }
    ],
    "trajectory_artifact": {
      "landing_zone": {"lat": 18.2, "lon": -67.1},
      "max_altitude_m": 115000
    }
  }
}
```

---

### Telemetry (WebSocket)

#### WS `/flights/{id}/telemetry`

Open a WebSocket connection to stream live telemetry during "In Flight" phase.

**Usage**:
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/flights/flight_001/telemetry');

ws.onmessage = (event) => {
  const telemetry = JSON.parse(event.data);
  console.log(telemetry);
  // {
  //   "timestamp": "2026-07-28T08:15:30Z",
  //   "altitude_m": 85000,
  //   "temperature_c": -45,
  //   "irradiance_w_m2": 1050,
  //   "gps_lat": 18.21,
  //   "gps_lon": -67.09
  // }
};
```

**Behavior**:
- Connection denied if flight state ≠ In Flight
- Emits telemetry updates as they arrive
- Connection closes automatically when flight transitions to Recovered

---

### Approvals

#### POST `/flights/{id}/approval`

Submit launch approval for a flight.

**Request**:
```json
{
  "approved_by": ["user_123", "user_456"],
  "basis_report": "All systems nominal, weather optimal, team ready"
}
```

**Authorization**: Only Captain, Co-Captain, or Chief_Engineer roles can approve.

**Response** (201):
```json
{
  "success": true,
  "data": {
    "id": "approval_001",
    "flight_id": "flight_001",
    "approved_by": ["user_123", "user_456"],
    "approved_at": "2026-07-27T14:00:00Z",
    "basis_report": "All systems nominal...",
    "external_notification_sent": true
  }
}
```

#### GET `/flights/{id}/approval`

Fetch approval record for a flight.

**Response** (200): Approval entity.

#### PUT `/flights/{id}/approval`

Update approval (extend basis report, add approver).

**Response** (200): Updated approval entity.

---

### Skills

#### GET `/missions/{id}/skills`

List skills (interactive workflows and checklists) available for a mission.

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "skill_001",
      "type": "interactive_workflow",
      "name": "Pre-Launch Payload Checklist",
      "description": "Verify payload systems before launch",
      "steps": [
        {
          "order": 1,
          "prompt": "Is the GPS unit powered and transmitting?",
          "expected_input": "text"
        }
      ]
    }
  ]
}
```

#### POST `/missions/{mission_id}/skills/{skill_id}/execute`

Trigger execution of a skill (copilot guides through interactive workflow or validates checklist).

**Request**:
```json
{
  "flight_id": "flight_001",
  "responses": {
    "step_1": "Yes, GPS is transmitting",
    "step_2": "Temperature sensor reading 22°C"
  }
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "skill_id": "skill_001",
    "execution_id": "exec_001",
    "status": "completed",
    "results": {
      "all_checks_passed": true,
      "timestamp": "2026-07-27T14:30:00Z"
    }
  }
}
```

---

## Error Codes

| Code | Meaning | HTTP Status |
|------|---------|------------|
| AUTH_INVALID | Invalid token or credentials | 401 |
| MISSION_NOT_FOUND | Mission ID doesn't exist | 404 |
| FLIGHT_NOT_FOUND | Flight ID doesn't exist | 404 |
| STATE_INVALID_TRANSITION | Cannot transition flight to requested state | 409 |
| PERMISSION_DENIED | User lacks required role for operation | 403 |
| VALIDATION_ERROR | Request body validation failed | 400 |
| TOOL_EXECUTION_FAILED | Weather/trajectory/airspace tool returned error | 500 |
| TELEMETRY_UNAVAILABLE | Flight not in "In Flight" state; WebSocket rejected | 403 |

---

## Rate Limiting

- **Unauthenticated**: 10 requests/minute
- **Authenticated**: 1000 requests/minute per user
- **Telemetry WebSocket**: No limit (connection-based)

Response headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1700000060
```

---

## Next: FastAPI Implementation

This spec unblocks backend implementation:
- `schemas.py`: Pydantic models (Mission, Flight, etc.)
- `main.py`: Route handlers
- `auth.py`: JWT middleware
- WebSocket handler for telemetry
