# STRATOS System Architecture Document (SAD)

## Version

v1.0

## Product

STRATOS

## Purpose

This System Architecture Document defines the high-level infrastructure, server architecture, third-party integrations, deployment model, and database schema for STRATOS.

STRATOS is an agent-assisted mission operations platform for LIFTS that supports mission planning, pre-flight readiness, live telemetry monitoring, trajectory prediction, post-flight data cleaning, scientific analysis, reporting, institutional knowledge retrieval, and Hermes-assisted workflows.

---

# 1. Architecture Goals

STRATOS must satisfy five primary architecture goals:

1. Keep mission operations reliable even when Hermes is unavailable.
2. Centralize mission state, telemetry, checklists, artifacts, and knowledge.
3. Support real-time telemetry ingestion and visualization.
4. Allow Hermes to interact with mission systems only through controlled backend tools.
5. Preserve LIFTS institutional knowledge through structured and semantic memory.

---

# 2. High-Level System Architecture

```text
Users
  |
  v
Next.js Web Application
  |
  |-- Mission Dashboard
  |-- Checklist UI
  |-- Telemetry Dashboard
  |-- Map View
  |-- Analysis UI
  |-- Hermes Chat UI
  |-- Artifact Renderer
  |
  v
FastAPI Backend
  |
  |-- Mission Service
  |-- Checklist Service
  |-- Telemetry Service
  |-- Prediction Service
  |-- Data Cleaning Service
  |-- Analysis Service
  |-- Artifact Service
  |-- Knowledge Ingestion Service
  |-- Hermes Gateway Service
  |
  v
Data and Storage Layer
  |
  |-- PostgreSQL or SQLite
  |-- pgvector or Supabase Vector
  |-- Object/File Storage
  |-- Obsidian Vault
  |-- SharePoint Files
  |
  v
Hermes Agent Runtime
  |
  |-- Mission Tools
  |-- Checklist Tools
  |-- Telemetry Tools
  |-- Knowledge Retrieval Tools
  |-- Prediction Tools
  |-- Data Cleaning Tools
  |-- Skill Execution
```

---

# 3. Infrastructure Overview

## MVP Infrastructure

```text
Frontend: Vercel
Backend: Render, Railway, Fly.io, or VPS
Database: Supabase PostgreSQL
Vector Store: Supabase Vector or pgvector
File Storage: Supabase Storage
Hermes Runtime: VPS or dedicated server
Obsidian Ingestion: Local vault sync
SharePoint Ingestion: Manual export first
```

## Local Development Infrastructure

```text
Frontend: Local Next.js dev server
Backend: Local FastAPI server
Database: SQLite
Vector Store: Local Chroma or Supabase dev project
File Storage: Local /storage directory
Hermes: Local or remote development instance
Telemetry Source: Simulator script
```

---

# 4. Server Setup

## Frontend Server

Technology:

- Next.js
- TypeScript
- React
- Tailwind CSS
- Leaflet for maps
- Recharts for charts
- WebSocket client for telemetry streams

Responsibilities:

- Render user interfaces.
- Display mission, checklist, telemetry, prediction, and artifact data.
- Send user requests to the backend.
- Display Hermes responses and generated artifacts.
- Maintain client-side session state.

The frontend must not call Hermes directly.

---

## Backend Server

Technology:

- FastAPI
- Python
- SQLAlchemy
- Pydantic
- Alembic migrations
- WebSocket support
- Celery, Redis Queue, or FastAPI background tasks

Responsibilities:

- Own mission state.
- Validate all API requests.
- Enforce role-based access control.
- Ingest and stream telemetry.
- Run prediction workflows.
- Run data cleaning jobs.
- Store artifacts.
- Serve knowledge search APIs.
- Mediate all Hermes access through Hermes Gateway.

---

## Hermes Runtime Server

Responsibilities:

- Natural language interaction.
- Tool orchestration.
- Knowledge retrieval.
- Workflow execution.
- Skill execution.
- Report drafting.
- Data interpretation.

Hermes must not directly mutate production databases. All operational actions must pass through backend-approved tools.

---

## Background Worker

Used for long-running or asynchronous jobs.

Responsibilities:

- Knowledge ingestion.
- File parsing.
- Embedding generation.
- Prediction jobs.
- Data cleaning jobs.
- Analysis report generation.
- Artifact generation.

Recommended MVP approach:

- Use FastAPI background tasks for simplest implementation.
- Move to Celery or Redis Queue if job volume increases.

---

# 5. Core Services

## Mission Service

Owns mission lifecycle state.

Capabilities:

- Create mission.
- Read mission.
- Update mission.
- Archive mission.
- Retrieve mission history.

## Checklist Service

Owns readiness tracking.

Capabilities:

- Generate checklist.
- Add checklist item.
- Update checklist item.
- Track completion.
- Link checklist items to documents.

## Telemetry Service

Owns live and historical telemetry.

Capabilities:

- Ingest telemetry.
- Validate telemetry.
- Store telemetry.
- Retrieve latest telemetry.
- Retrieve historical telemetry.
- Stream telemetry through WebSockets.

## Prediction Service

Owns trajectory prediction workflows.

Capabilities:

- Run prediction.
- Store prediction.
- Retrieve prediction.
- Compare prediction against actual telemetry.

## Data Cleaning Service

Owns post-flight dataset processing.

Capabilities:

- Validate uploaded datasets.
- Detect missing values.
- Detect outliers.
- Normalize timestamps.
- Interpolate missing data.
- Smooth noisy data.
- Generate cleaned datasets.
- Produce cleaning summaries.

## Analysis Service

Owns scientific interpretation outputs.

Capabilities:

- Generate plots.
- Compute statistics.
- Compare flights.
- Detect unusual sensor behavior.
- Generate analysis report drafts.

## Artifact Service

Owns structured outputs.

Supported artifact types:

- Map
- Chart
- Table
- Report
- Checklist
- Timeline
- Alert

## Knowledge Ingestion Service

Owns institutional knowledge indexing.

Capabilities:

- Parse Obsidian notes.
- Parse SharePoint exports.
- Extract metadata.
- Chunk documents.
- Generate embeddings.
- Store chunks in vector database.
- Preserve source attribution.

## Hermes Gateway Service

Controls all communication between STRATOS and Hermes.

Responsibilities:

- Authentication.
- User context injection.
- Mission context injection.
- Tool permission checks.
- Autonomy enforcement.
- Tool call logging.
- Approval handling.
- Artifact extraction.
- Response normalization.

---

# 6. Third-Party API Integrations

## Required MVP Integrations

### Hermes Agent

Purpose:

- Mission assistant.
- Workflow automation.
- Knowledge retrieval.
- Skill execution.

Integration pattern:

```text
Frontend -> FastAPI Hermes Gateway -> Hermes Agent -> Backend Tools
```

### Supabase PostgreSQL

Purpose:

- Production relational database.
- Mission data.
- Checklist data.
- Telemetry data.
- Artifacts.
- Tool logs.
- User roles.

### Supabase Vector or pgvector

Purpose:

- Semantic search.
- Knowledge retrieval.
- Source-grounded Hermes responses.

### Supabase Storage or Object Storage

Purpose:

- Telemetry files.
- Cleaned datasets.
- Generated reports.
- Exported artifacts.
- Uploaded documents.

### Tawhiri or Custom Prediction Tool

Purpose:

- High-altitude balloon trajectory prediction.
- Landing estimate generation.
- Prediction artifact creation.

---

## Phase 2 Integrations

### Microsoft Graph API

Purpose:

- SharePoint document ingestion.
- File metadata extraction.
- Scheduled synchronization.
- Version tracking.

### NOAA Data Sources

Purpose:

- Weather context.
- Atmospheric data.
- Prediction enhancement.

### APRS

Purpose:

- Live balloon tracking.
- Telemetry ingestion from radio systems.

### Radiosonde Systems

Purpose:

- Atmospheric profile ingestion.
- Validation against balloon telemetry.

---

# 7. Database Architecture

STRATOS uses hybrid memory:

1. Relational database for operational truth.
2. Vector database for semantic knowledge.
3. Object storage for files and generated outputs.

The relational database is the source of truth for operational facts. If Hermes or vector retrieval conflicts with the database, the database wins.

---

# 8. Relational Database Schema

## users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('member', 'mission_lead', 'admin')),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## missions

```sql
CREATE TABLE missions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    launch_date TIMESTAMP,
    launch_lat DOUBLE PRECISION,
    launch_lon DOUBLE PRECISION,
    status TEXT NOT NULL CHECK (
        status IN ('planning', 'ready', 'active', 'recovered', 'archived')
    ),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## checklist_items

```sql
CREATE TABLE checklist_items (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    description TEXT,
    category TEXT,
    completed BOOLEAN NOT NULL DEFAULT false,
    completed_by UUID REFERENCES users(id),
    completed_at TIMESTAMP,
    source TEXT NOT NULL CHECK (source IN ('manual', 'hermes', 'template')),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## telemetry_points

```sql
CREATE TABLE telemetry_points (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    altitude_m DOUBLE PRECISION,
    battery_pct DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION,
    pressure_hpa DOUBLE PRECISION,
    humidity_pct DOUBLE PRECISION,
    raw_payload JSONB,
    quality_flag TEXT NOT NULL CHECK (
        quality_flag IN ('valid', 'suspect', 'invalid', 'cleaned')
    ),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

Recommended indexes:

```sql
CREATE INDEX idx_telemetry_mission_timestamp
ON telemetry_points (mission_id, timestamp DESC);

CREATE INDEX idx_telemetry_mission_quality
ON telemetry_points (mission_id, quality_flag);
```

## predictions

```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('tawhiri', 'custom')),
    input_parameters JSONB NOT NULL,
    trajectory JSONB NOT NULL,
    landing_lat DOUBLE PRECISION,
    landing_lon DOUBLE PRECISION,
    estimated_flight_time_s INTEGER,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## artifacts

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    mission_id UUID REFERENCES missions(id) ON DELETE SET NULL,
    artifact_type TEXT NOT NULL CHECK (
        artifact_type IN ('map', 'chart', 'table', 'report', 'checklist', 'timeline', 'alert')
    ),
    title TEXT NOT NULL,
    description TEXT,
    payload JSONB NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## skill_metadata

```sql
CREATE TABLE skill_metadata (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT NOT NULL DEFAULT 'LIFTS',
    created_by TEXT NOT NULL,
    creation_type TEXT NOT NULL CHECK (creation_type IN ('explicit', 'learned')),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'deprecated')),
    version TEXT NOT NULL,
    last_used_at TIMESTAMP,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## data_cleaning_jobs

```sql
CREATE TABLE data_cleaning_jobs (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    input_dataset_path TEXT NOT NULL,
    output_dataset_path TEXT,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    methods_used JSONB,
    summary JSONB,
    error_message TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    completed_at TIMESTAMP
);
```

## document_chunks

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    source_path TEXT NOT NULL,
    document_title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding_id TEXT,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## hermes_tool_logs

```sql
CREATE TABLE hermes_tool_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    mission_id UUID REFERENCES missions(id),
    tool_name TEXT NOT NULL,
    permission_level INTEGER NOT NULL CHECK (permission_level IN (1, 2, 3)),
    inputs JSONB,
    outputs JSONB,
    side_effects BOOLEAN NOT NULL DEFAULT false,
    approval_status TEXT CHECK (
        approval_status IN ('not_required', 'approved', 'rejected', 'pending')
    ),
    undo_supported BOOLEAN NOT NULL DEFAULT false,
    undo_payload JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

---

# 9. Vector Database Schema

Each embedded chunk should store:

```json
{
  "id": "uuid",
  "content": "string",
  "embedding": "vector",
  "source": "obsidian | sharepoint | mission_report | telemetry_analysis",
  "source_path": "string",
  "document_title": "string",
  "author": "string | null",
  "created_at": "datetime | null",
  "updated_at": "datetime | null",
  "project": "string | null",
  "mission_id": "uuid | null",
  "document_type": "procedure | report | checklist | analysis | note",
  "chunk_index": "integer",
  "content_hash": "string"
}
```

Search should return:

```json
{
  "chunk_id": "uuid",
  "content": "string",
  "source_path": "string",
  "document_title": "string",
  "score": "float",
  "metadata": {}
}
```

Hermes must cite retrieved sources when answering knowledge-based questions.

---

# 10. File Storage Layout

Recommended object storage structure:

```text
/storage
  /missions
    /{mission_id}
      /telemetry
        raw/
        cleaned/
      /predictions
      /artifacts
      /reports
  /knowledge
    /obsidian
    /sharepoint
  /exports
```

Files that should be stored:

- Raw telemetry CSV and JSON.
- Cleaned telemetry datasets.
- Prediction outputs.
- Generated reports.
- Chart exports.
- Map exports.
- Uploaded documentation.

---

# 11. API Boundary

The frontend communicates only with the FastAPI backend.

```text
Frontend -> FastAPI Backend -> Database
Frontend -> FastAPI Backend -> Hermes Gateway -> Hermes
Frontend -> FastAPI Backend -> Object Storage
Frontend -> FastAPI Backend -> Vector Store
```

The frontend must not directly access:

- Hermes runtime.
- Database credentials.
- Vector database credentials.
- Object storage credentials.
- Prediction tool credentials.

---

# 12. Authentication and Authorization

## Roles

### Member

Can:

- View missions.
- View telemetry.
- Ask Hermes questions.
- Run read-only workflows.
- Upload datasets.

### Mission Lead

Can:

- Create missions.
- Modify checklists.
- Run predictions.
- Approve operational changes.
- Generate reports.

### Admin

Can:

- Delete or archive missions.
- Manage users.
- Manage integrations.
- Approve shell commands.
- Approve system-level actions.

---

# 13. Hermes Autonomy Enforcement

Hermes actions are divided into three permission levels.

## Level 1: Read Operations

Execution:

- Execute immediately.
- Log action.

Examples:

- Query mission.
- Read telemetry.
- Search documents.
- Generate draft reports.

## Level 2: Operational Changes

Execution:

- Execute.
- Notify user.
- Store undo action when possible.
- Log action.

Examples:

- Update checklist item.
- Create artifact.
- Modify mission metadata.
- Create skill.

## Level 3: Administrative or System Actions

Execution:

- Require explicit approval.
- Log approval.
- Execute in sandbox where possible.

Examples:

- Shell command execution.
- Code execution.
- Mission deletion.
- System configuration changes.

The backend enforces autonomy. Hermes must not self-enforce permissions.

---

# 14. Telemetry Architecture

## Real-Time Flow

```text
Telemetry Source
  |
  v
POST /api/missions/{mission_id}/telemetry
  |
  v
Validation
  |
  v
Database Write
  |
  v
WebSocket Broadcast
  |
  v
Telemetry Dashboard
```

## Validation Rules

- Timestamp must be present.
- Latitude must be between -90 and 90.
- Longitude must be between -180 and 180.
- Battery must be between 0 and 100.
- Altitude must be within expected mission range.
- Duplicate timestamps should be flagged.
- Malformed sensor values should be marked invalid.

---

# 15. Knowledge Ingestion Architecture

```text
Obsidian / SharePoint / Mission Reports
  |
  v
Connector
  |
  v
Parser
  |
  v
Metadata Extractor
  |
  v
Chunker
  |
  v
Embedding Generator
  |
  v
Vector Database
  |
  v
Knowledge Search API
  |
  v
Hermes
```

MVP ingestion should support manual triggering. Phase 2 should add scheduled ingestion and SharePoint webhook support.

---

# 16. Data Cleaning Architecture

```text
Dataset Upload
  |
  v
Schema Detection
  |
  v
Validation
  |
  v
Cleaning Job Creation
  |
  v
Background Worker
  |
  v
Cleaned Dataset + Summary JSON
  |
  v
Chart Artifacts
  |
  v
Hermes Interpretation
  |
  v
Report Artifact
```

MVP methods:

- Missing value detection.
- Linear interpolation.
- Time interpolation.
- Duplicate row removal.
- Timestamp normalization.
- Z-score outlier detection.
- IQR outlier detection.
- Rolling average smoothing.

Raw data must always be preserved.

---

# 17. Deployment Architecture

## MVP Deployment Diagram

```text
Vercel
  |
  v
FastAPI Backend on Render/Railway/Fly.io/VPS
  |
  |-- Supabase PostgreSQL
  |-- Supabase Vector / pgvector
  |-- Supabase Storage
  |-- Hermes VPS
  |-- Prediction Tool
```

## Recommended MVP Defaults

- Frontend: Vercel
- Backend: Render or VPS
- Database: Supabase PostgreSQL
- Vector Database: Supabase Vector
- File Storage: Supabase Storage
- Map UI: Leaflet
- Charts: Recharts
- Data Processing: pandas, numpy, scipy
- Background Jobs: FastAPI background tasks first
- Hermes Hosting: VPS
- SharePoint Ingestion: manual export first
- Obsidian Ingestion: local vault sync
- Telemetry Format: CSV and JSON first

---

# 18. Observability

STRATOS should log:

- API requests.
- Authentication events.
- Mission mutations.
- Checklist updates.
- Telemetry ingestion events.
- WebSocket events.
- Prediction jobs.
- Data cleaning jobs.
- Knowledge ingestion jobs.
- Hermes tool calls.
- Skill executions.
- Level 2 and Level 3 approvals.

Metrics to track:

- API latency.
- Telemetry ingestion rate.
- WebSocket uptime.
- Hermes response time.
- Prediction runtime.
- Data cleaning runtime.
- Knowledge retrieval success rate.
- Artifact generation success rate.

---

# 19. Failure Handling

## Hermes Failure

System behavior:

- Mission dashboard remains available.
- Telemetry dashboard remains available.
- Checklists remain available.
- Uploads remain available.
- Hermes chat and agent workflows are disabled.

## Database Failure

System behavior:

- Return service unavailable.
- Stop accepting new telemetry writes.
- Preserve queued telemetry where possible.
- Alert admin.

## Telemetry Failure

System behavior:

- Mark telemetry stream as stale.
- Display last received point.
- Preserve historical telemetry.
- Alert mission users.

## Prediction Failure

System behavior:

- Store failed job.
- Preserve input parameters.
- Display error.
- Allow retry.

## Data Cleaning Failure

System behavior:

- Preserve raw dataset.
- Store error message.
- Mark job as failed.
- Allow retry with different method.

## Knowledge Ingestion Failure

System behavior:

- Store failed document path.
- Continue indexing other files.
- Report failures to admin.

---

# 20. Security Requirements

- Backend owns all credentials.
- Frontend never stores service keys.
- Hermes cannot directly write to the database.
- Level 3 actions require explicit approval.
- Shell execution must be sandboxed.
- Production credentials must not be available inside command sandboxes.
- All Hermes tool calls must be logged.
- All Level 2 and Level 3 actions must be auditable.
- Raw telemetry and cleaned datasets must be retained separately.

---

# 21. Open Architecture Decisions

1. Final production backend host: Render, Railway, Fly.io, or VPS.
2. Final vector database: Supabase Vector, pgvector, Chroma, or Qdrant.
3. Exact Hermes hosting model: local, VPS, or backend-adjacent service.
4. Exact telemetry schema standard for LIFTS.
5. Exact SharePoint ingestion path: Microsoft Graph API or manual export.
6. Sandbox design for shell and code execution.
7. Auth provider: simple login, institutional OAuth, or Supabase Auth.
8. First supported telemetry file formats: CSV, JSON, or both.
9. Skill storage format and versioning strategy.
10. Production backup and restore strategy.

---

# 22. Architecture Position

STRATOS should be built as a deterministic mission operations platform first and an agent-assisted intelligence system second.

The backend owns operational truth, permissions, mission state, telemetry, artifacts, and logs.

Hermes owns natural language interaction, workflow assistance, retrieval, analysis support, and skill execution.

This separation keeps STRATOS reliable during real mission operations while still allowing Hermes to improve LIFTS workflows over time.
