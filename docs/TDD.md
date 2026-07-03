# STRATOS Technical Design Document (TDD)

## Version

v1.0

## Product

STRATOS

## Purpose

This Technical Design Document defines the system architecture, services, data models, APIs, pipelines, autonomy boundaries, and implementation plan for STRATOS.

STRATOS is an agent-assisted mission operations platform for LIFTS. It supports pre-flight planning, flight operations, telemetry monitoring, post-flight data cleaning, scientific analysis, and institutional knowledge retrieval through Hermes.

---

# 1. System Overview

STRATOS consists of four major layers:

1. Experience Layer
2. Hermes Intelligence Layer
3. Operational Layer
4. Knowledge Layer

The system is designed so that core mission operations remain usable even if Hermes is unavailable. Hermes enhances the system through chat, workflow automation, skill execution, knowledge retrieval, and data analysis.

---

# 2. High-Level Architecture

```text
User
  |
  v
Next.js Web App
  |
  |---- Mission UI
  |---- Checklist UI
  |---- Telemetry Dashboard
  |---- Data Analysis UI
  |---- Hermes Chat UI
  |---- Artifact Renderer
  |
  v
FastAPI Backend
  |
  |---- Mission Service
  |---- Checklist Service
  |---- Telemetry Service
  |---- Artifact Service
  |---- Data Cleaning Service
  |---- Knowledge Ingestion Service
  |---- Hermes Gateway Service
  |
  v
Storage Layer
  |
  |---- PostgreSQL or SQLite
  |---- Vector Database
  |---- Object/File Storage
  |---- Obsidian Vault
  |---- SharePoint Files
  |
  v
Hermes Agent
  |
  |---- Skills
  |---- Memory
  |---- Tool Execution
  |---- Browser Access
  |---- Terminal Access
```

---

# 3. Technology Stack

## Frontend

- Next.js
- TypeScript
- React
- Tailwind CSS
- Map rendering library
- Charting library
- WebSocket client

## Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic
- Celery or background task worker
- WebSocket support

## Database

MVP:

- SQLite for local development

Preferred production path:

- PostgreSQL

## Vector Storage

Options:

- Supabase Vector
- pgvector
- Chroma
- Qdrant

Recommended MVP:

- Supabase Vector or pgvector

## Agent Runtime

- Hermes Agent

## Tool Execution

- Hermes native tools
- CLI-Anything where appropriate
- Custom Python tools
- Tawhiri prediction integration

## File and Knowledge Sources

- Obsidian Vault
- SharePoint
- Mission documents
- Flight reports
- Telemetry files

---

# 4. Core Design Principle

STRATOS must separate operational reliability from agent intelligence.

Core system functions must work without Hermes:

- Create missions
- View telemetry
- Update checklists
- Upload telemetry files
- View previous mission data

Hermes enhances the platform:

- Natural language interaction
- Workflow execution
- Data interpretation
- Skill generation
- Knowledge retrieval
- Report generation

---

# 5. Experience Layer

## Responsibilities

The Experience Layer provides all user-facing interfaces.

## Interfaces

### Mission Dashboard

Displays:

- Mission name
- Launch date
- Mission status
- Launch coordinates
- Checklist progress
- Latest telemetry
- Prediction summary

### Pre-Flight Tab

Displays:

- Dynamic checklist
- Readiness status
- Required documentation
- Hermes readiness recommendations

### Flight Tab

Displays:

- Live telemetry
- Map visualization
- Predicted trajectory
- Actual trajectory
- Alerts
- Mission status summary

### Post-Flight Tab

Displays:

- Uploaded telemetry datasets
- Cleaning results
- Analysis charts
- Generated reports
- Export options

### Hermes Chat Tab

Allows users to:

- Ask mission questions
- Execute workflows
- Generate reports
- Query documentation
- Request data analysis
- Trigger skills

### Artifact Renderer

Renders structured outputs from Hermes and backend services.

Supported artifact types:

- Map
- Chart
- Table
- Report
- Checklist
- Timeline
- Alert

---

# 6. Hermes Intelligence Layer

## Responsibilities

Hermes is the intelligence layer of STRATOS.

Hermes handles:

- Natural language interaction
- Skill execution
- Skill creation
- Workflow automation
- Knowledge retrieval
- Tool orchestration
- Data interpretation
- New member onboarding

## Hermes Access

Hermes can access:

- Mission API
- Checklist API
- Telemetry API
- Artifact API
- Knowledge search API
- Data cleaning API
- Prediction tools
- Browser tools
- Terminal tools

## Hermes Gateway Service

STRATOS should not allow the frontend to call Hermes directly.

Instead, all Hermes communication should pass through a backend service:

```text
Frontend
  |
  v
FastAPI Hermes Gateway
  |
  v
Hermes Agent
```

The gateway handles:

- Authentication
- User context
- Mission context
- Permission checks
- Tool access boundaries
- Logging
- Response normalization
- Artifact extraction

---

# 7. Operational Layer

The Operational Layer contains deterministic backend services.

## Services

### Mission Service

Manages mission records.

Capabilities:

- Create mission
- Read mission
- Update mission
- Archive mission
- Retrieve mission history

### Checklist Service

Manages pre-flight readiness.

Capabilities:

- Generate checklist
- Add checklist item
- Update checklist item
- Track completion
- Link checklist items to documents

### Telemetry Service

Handles real-time and historical telemetry.

Capabilities:

- Ingest telemetry
- Store telemetry
- Retrieve latest telemetry
- Retrieve historical telemetry
- Stream telemetry to frontend
- Validate telemetry fields

### Prediction Service

Handles trajectory predictions.

Capabilities:

- Run trajectory prediction
- Store prediction result
- Retrieve previous prediction
- Compare prediction vs actual telemetry

### Data Cleaning Service

Handles post-flight scientific processing.

Capabilities:

- Detect anomalies
- Remove invalid points
- Interpolate missing values
- Correct timestamp inconsistencies
- Smooth noisy sensor data
- Generate cleaned dataset
- Produce cleaning summary

### Analysis Service

Handles scientific interpretation.

Capabilities:

- Generate plots
- Compare flights
- Compute summary statistics
- Identify trends
- Detect unusual sensor behavior
- Generate analysis report

### Artifact Service

Stores and retrieves structured outputs.

Capabilities:

- Create artifact
- Retrieve artifact
- Update artifact metadata
- Render artifact payloads in frontend

---

# 8. Knowledge Layer

The Knowledge Layer stores institutional memory and documentation.

## Sources

- Obsidian Vault
- SharePoint
- Mission Reports
- Flight Logs
- Historical Discussions
- Team Procedures
- Telemetry Analysis Results

## Knowledge Types

### Structured Knowledge

Stored in relational database:

- Missions
- Checklists
- Telemetry
- Users
- Artifacts
- Skill metadata

### Semantic Knowledge

Stored in vector database:

- Documentation chunks
- Mission report sections
- Lessons learned
- Procedure descriptions
- Analysis summaries
- Historical notes

---

# 9. Knowledge Ingestion Pipeline

## Pipeline Flow

```text
Source Documents
  |
  v
File Connector
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
Retrieval API
```

## Sources

### Obsidian

Supported files:

- Markdown files
- Linked notes
- Mission logs
- Procedure notes

### SharePoint

Supported files:

- PDF
- DOCX
- XLSX
- CSV
- Markdown
- Text files

## Metadata Schema

Each indexed chunk should include:

```json
{
  "source": "obsidian | sharepoint | mission_report | telemetry_analysis",
  "source_path": "string",
  "document_title": "string",
  "author": "string | null",
  "created_at": "datetime | null",
  "updated_at": "datetime | null",
  "project": "string | null",
  "mission_id": "string | null",
  "document_type": "procedure | report | checklist | analysis | note",
  "chunk_index": "integer",
  "content_hash": "string"
}
```

## Indexing Strategy

MVP:

- Manual ingestion trigger
- Re-index changed files
- Store metadata
- Support source citation

Phase 2:

- Scheduled ingestion
- SharePoint webhook integration
- Obsidian file watcher
- Duplicate detection
- Document versioning

---

# 10. Memory Architecture

STRATOS uses hybrid memory.

## Structured Memory

Relational database stores operational facts.

Examples:

- Mission Alpha launched on a date
- Checklist item is complete
- Latest altitude is a value
- Sensor payload has specific fields

## Semantic Memory

Vector database stores contextual knowledge.

Examples:

- Why a previous mission failed
- How LIFTS performs recovery
- What procedure to follow before launch
- How a sensor dataset should be interpreted

## Source of Truth Rule

The relational database is the source of truth for operational facts.

Hermes memory and vector retrieval provide context, explanations, and historical knowledge.

If database information conflicts with semantic memory, the database wins.

---

# 11. Data Model

## Mission

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "launch_date": "datetime",
  "launch_lat": "float",
  "launch_lon": "float",
  "status": "planning | ready | active | recovered | archived",
  "created_by": "user_id",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## ChecklistItem

```json
{
  "id": "uuid",
  "mission_id": "uuid",
  "label": "string",
  "description": "string",
  "category": "string",
  "completed": "boolean",
  "completed_by": "user_id | null",
  "completed_at": "datetime | null",
  "source": "manual | hermes | template",
  "created_at": "datetime"
}
```

## TelemetryPoint

```json
{
  "id": "uuid",
  "mission_id": "uuid",
  "timestamp": "datetime",
  "lat": "float | null",
  "lon": "float | null",
  "altitude_m": "float | null",
  "battery_pct": "float | null",
  "temperature_c": "float | null",
  "pressure_hpa": "float | null",
  "humidity_pct": "float | null",
  "raw_payload": "json",
  "quality_flag": "valid | suspect | invalid | cleaned",
  "created_at": "datetime"
}
```

## Prediction

```json
{
  "id": "uuid",
  "mission_id": "uuid",
  "provider": "tawhiri | custom",
  "input_parameters": "json",
  "trajectory": "json",
  "landing_lat": "float",
  "landing_lon": "float",
  "estimated_flight_time_s": "integer",
  "created_by": "user_id | hermes",
  "created_at": "datetime"
}
```

## Artifact

```json
{
  "id": "uuid",
  "mission_id": "uuid | null",
  "artifact_type": "map | chart | table | report | checklist | timeline | alert",
  "title": "string",
  "payload": "json",
  "created_by": "user_id | hermes",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## SkillMetadata

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "owner": "LIFTS",
  "created_by": "hermes | user_id",
  "creation_type": "explicit | learned",
  "status": "draft | active | deprecated",
  "version": "string",
  "last_used_at": "datetime | null",
  "usage_count": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## DocumentChunk

```json
{
  "id": "uuid",
  "source": "string",
  "source_path": "string",
  "document_title": "string",
  "content": "string",
  "metadata": "json",
  "embedding_id": "string",
  "content_hash": "string",
  "created_at": "datetime"
}
```

## DataCleaningJob

```json
{
  "id": "uuid",
  "mission_id": "uuid",
  "input_dataset_path": "string",
  "output_dataset_path": "string | null",
  "status": "queued | running | completed | failed",
  "methods_used": "json",
  "summary": "json",
  "created_by": "user_id | hermes",
  "created_at": "datetime",
  "completed_at": "datetime | null"
}
```

---

# 12. API Design

## Mission APIs

```http
POST /api/missions
GET /api/missions
GET /api/missions/{mission_id}
PATCH /api/missions/{mission_id}
POST /api/missions/{mission_id}/archive
```

## Checklist APIs

```http
GET /api/missions/{mission_id}/checklist
POST /api/missions/{mission_id}/checklist
PATCH /api/checklist/{item_id}
POST /api/missions/{mission_id}/checklist/generate
```

## Telemetry APIs

```http
POST /api/missions/{mission_id}/telemetry
GET /api/missions/{mission_id}/telemetry/latest
GET /api/missions/{mission_id}/telemetry/history
GET /api/missions/{mission_id}/telemetry/stream
POST /api/missions/{mission_id}/telemetry/upload
```

## Prediction APIs

```http
POST /api/missions/{mission_id}/predictions
GET /api/missions/{mission_id}/predictions
GET /api/predictions/{prediction_id}
```

## Data Cleaning APIs

```http
POST /api/missions/{mission_id}/cleaning-jobs
GET /api/cleaning-jobs/{job_id}
GET /api/cleaning-jobs/{job_id}/results
POST /api/cleaning-jobs/{job_id}/approve
```

## Artifact APIs

```http
POST /api/artifacts
GET /api/artifacts/{artifact_id}
GET /api/missions/{mission_id}/artifacts
```

## Knowledge APIs

```http
POST /api/knowledge/ingest
GET /api/knowledge/search
GET /api/knowledge/sources/{source_id}
```

## Hermes APIs

```http
POST /api/hermes/chat
POST /api/hermes/execute
GET /api/hermes/sessions/{session_id}
POST /api/hermes/skills
GET /api/hermes/skills
GET /api/hermes/skills/{skill_id}
```

---

# 13. Hermes Tool Interface

Hermes should access backend functionality through explicit tools.

## Tool Definition Pattern

Each tool should define:

- Name
- Description
- Inputs
- Outputs
- Permission level
- Side effects
- Undo behavior

## Example Tool: Query Mission

```json
{
  "name": "query_mission",
  "description": "Retrieve mission details by mission ID or name.",
  "permission_level": 1,
  "inputs": {
    "mission_id": "string | null",
    "mission_name": "string | null"
  },
  "outputs": {
    "mission": "Mission"
  },
  "side_effects": false,
  "undo_supported": false
}
```

## Example Tool: Update Checklist Item

```json
{
  "name": "update_checklist_item",
  "description": "Mark a checklist item as complete or incomplete.",
  "permission_level": 2,
  "inputs": {
    "item_id": "string",
    "completed": "boolean"
  },
  "outputs": {
    "updated_item": "ChecklistItem"
  },
  "side_effects": true,
  "undo_supported": true
}
```

## Example Tool: Execute Shell Command

```json
{
  "name": "execute_shell_command",
  "description": "Execute an approved shell command in a sandboxed environment.",
  "permission_level": 3,
  "inputs": {
    "command": "string",
    "working_directory": "string"
  },
  "outputs": {
    "stdout": "string",
    "stderr": "string",
    "exit_code": "integer"
  },
  "side_effects": true,
  "undo_supported": false
}
```

---

# 14. Autonomy Enforcement

The backend must enforce autonomy rules. Hermes should not be trusted to self-enforce permissions.

## Level 1

Read operations.

Behavior:

- Execute immediately
- Log action

Examples:

- Read telemetry
- Query mission
- Search documents
- Generate report drafts

## Level 2

Operational changes.

Behavior:

- Execute
- Notify user
- Store undo action if possible

Examples:

- Update checklist
- Create mission artifact
- Modify mission metadata
- Create skill

## Level 3

Administrative or system actions.

Behavior:

- Require explicit approval before execution
- Log approval
- Execute in sandbox where possible

Examples:

- Shell commands
- Code execution
- System configuration changes
- Mission deletion

---

# 15. Telemetry Pipeline

## Real-Time Telemetry Flow

```text
Telemetry Source
  |
  v
Telemetry Ingestion API
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
Frontend Telemetry Dashboard
```

## Telemetry Validation

Validation checks:

- Timestamp present
- Latitude and longitude within valid range
- Altitude within expected range
- Battery value within 0-100
- Sensor values parse correctly
- Duplicate timestamp detection

## Telemetry Quality Flags

- valid
- suspect
- invalid
- cleaned

---

# 16. Data Cleaning Pipeline

## Post-Flight Cleaning Flow

```text
Raw Dataset Upload
  |
  v
Schema Detection
  |
  v
Validation
  |
  v
Anomaly Detection
  |
  v
Cleaning Method Selection
  |
  v
Cleaning Execution
  |
  v
Cleaned Dataset
  |
  v
Charts and Summary
  |
  v
Hermes Interpretation
  |
  v
Report Artifact
```

## MVP Cleaning Methods

- Missing value detection
- Linear interpolation
- Time interpolation
- Outlier detection using z-score
- Outlier detection using interquartile range
- Basic rolling average smoothing
- Timestamp normalization
- Duplicate row removal

## Phase 2 Cleaning Methods

- Wavelet denoising
- Sensor fusion
- Kalman filtering
- Advanced anomaly detection
- Cross-sensor validation
- Automated method recommendation

## Cleaning Output

Each cleaning job should generate:

- Cleaned CSV
- Summary JSON
- Anomaly report
- Before and after chart artifacts
- Recommended interpretation notes

---

# 17. Prediction Pipeline

## Prediction Flow

```text
Mission Launch Parameters
  |
  v
Prediction Request
  |
  v
Prediction Tool or Tawhiri Integration
  |
  v
Trajectory Result
  |
  v
Prediction Storage
  |
  v
Map Artifact
```

## Prediction Inputs

- Launch latitude
- Launch longitude
- Launch altitude
- Launch time
- Ascent rate
- Descent rate
- Burst altitude
- Balloon parameters

## Prediction Outputs

- Trajectory path
- Estimated landing point
- Estimated flight time
- Map artifact
- Recovery recommendation summary

---

# 18. Artifact Schema

## Base Artifact

```json
{
  "artifact_type": "string",
  "title": "string",
  "description": "string",
  "payload": {},
  "metadata": {
    "mission_id": "string | null",
    "created_by": "string",
    "created_at": "datetime"
  }
}
```

## Map Artifact Payload

```json
{
  "center": {
    "lat": "float",
    "lon": "float"
  },
  "zoom": "integer",
  "layers": [
    {
      "name": "Predicted Trajectory",
      "type": "polyline",
      "points": [
        {
          "lat": "float",
          "lon": "float",
          "altitude_m": "float | null",
          "timestamp": "datetime | null"
        }
      ]
    }
  ],
  "markers": [
    {
      "label": "Predicted Landing",
      "lat": "float",
      "lon": "float",
      "metadata": {}
    }
  ]
}
```

## Chart Artifact Payload

```json
{
  "chart_type": "line | scatter | bar",
  "x_axis": {
    "label": "string",
    "field": "string"
  },
  "y_axis": {
    "label": "string",
    "field": "string"
  },
  "series": [
    {
      "name": "string",
      "data": [
        {
          "x": "number | string",
          "y": "number"
        }
      ]
    }
  ]
}
```

## Report Artifact Payload

```json
{
  "sections": [
    {
      "heading": "string",
      "content": "string",
      "sources": [
        {
          "title": "string",
          "source_path": "string"
        }
      ]
    }
  ]
}
```

---

# 19. Security and Access Control

## Authentication

MVP options:

- Simple team login
- OAuth through institutional account
- Admin-created accounts

Recommended:

- Role-based accounts from the start

## Roles

### Member

Can:

- View missions
- View telemetry
- Ask Hermes questions
- Run read-only workflows
- Upload datasets

### Mission Lead

Can:

- Create missions
- Modify checklists
- Run predictions
- Approve operational changes

### Admin

Can:

- Delete missions
- Approve shell commands
- Manage integrations
- Manage users
- Approve system-level actions

## Logging

Log all Hermes actions:

- User
- Timestamp
- Tool called
- Inputs
- Outputs
- Permission level
- Approval status
- Undo availability

---

# 20. Error Handling

## Hermes Failure

If Hermes is unavailable:

- Mission dashboard remains usable
- Telemetry dashboard remains usable
- Checklists remain usable
- Data uploads remain possible
- Chat and agent workflows are disabled

## Prediction Failure

If prediction tool fails:

- Store failed job
- Display error
- Allow retry
- Preserve input parameters

## Data Cleaning Failure

If cleaning fails:

- Preserve raw dataset
- Store error trace
- Mark job as failed
- Allow retry with different method

## Knowledge Ingestion Failure

If ingestion fails:

- Store failed document path
- Store error type
- Continue indexing other documents
- Report failed files to admin

---

# 21. Observability

## Logs

Required logs:

- API requests
- Telemetry ingestion events
- Hermes tool calls
- Skill executions
- Knowledge ingestion jobs
- Data cleaning jobs
- Prediction jobs

## Metrics

Track:

- API latency
- Telemetry ingestion rate
- WebSocket uptime
- Hermes response time
- Prediction runtime
- Data cleaning runtime
- Knowledge retrieval success rate

## Audit Trail

Every Level 2 and Level 3 Hermes action must be auditable.

---

# 22. Deployment Architecture

## MVP Deployment

Recommended:

- Frontend: Vercel
- Backend: Render, Railway, Fly.io, or VPS
- Database: Supabase PostgreSQL
- Vector DB: Supabase Vector or pgvector
- File Storage: Supabase Storage or local volume
- Hermes: VPS or dedicated server

## Local Development

```text
Next.js frontend
FastAPI backend
SQLite database
Local vector DB or Supabase dev project
Local Hermes instance
Local Obsidian vault
Mock SharePoint connector
```

---

# 23. Implementation Plan

## Phase 0: Foundation

Deliverables:

- Repo setup
- Frontend scaffold
- Backend scaffold
- Database schema
- Authentication placeholder
- Basic mission CRUD

## Phase 1: Mission and Checklist System

Deliverables:

- Mission dashboard
- Mission creation flow
- Checklist tab
- Checklist update API
- Checklist templates

## Phase 2: Telemetry System

Deliverables:

- Telemetry ingestion API
- Telemetry simulator
- Telemetry database model
- Live telemetry dashboard
- Map visualization
- WebSocket streaming

## Phase 3: Hermes Integration

Deliverables:

- Hermes Gateway API
- Chat UI
- Mission query tools
- Checklist tools
- Telemetry query tools
- Permission enforcement
- Tool call logging

## Phase 4: Knowledge Layer

Deliverables:

- Obsidian ingestion
- SharePoint ingestion
- Document chunking
- Metadata extraction
- Vector search
- Source citation support

## Phase 5: Prediction Workflows

Deliverables:

- Tawhiri or prediction integration
- Prediction API
- Prediction storage
- Map artifact rendering
- Prediction vs actual comparison

## Phase 6: Data Cleaning and Analysis

Deliverables:

- Dataset upload
- Cleaning job runner
- Outlier detection
- Interpolation
- Smoothing
- Chart artifact generation
- Hermes analysis summary
- Report artifact generation

## Phase 7: Skills System

Deliverables:

- Skill metadata model
- Hermes skill execution
- Explicit skill creation
- Experimental learned skill creation
- Skill reuse tracking

---

# 24. MVP Definition of Done

The TDD MVP is complete when:

- Users can create and manage missions
- Users can generate and update checklists
- Telemetry can be ingested and visualized
- Live telemetry can be displayed on a map
- Hermes can answer mission questions through the gateway
- Hermes can query mission data through tools
- Hermes can retrieve Obsidian and SharePoint knowledge
- Hermes can cite knowledge sources
- Prediction workflows generate map artifacts
- Users can upload telemetry datasets
- Data cleaning jobs produce cleaned datasets
- Analysis charts can be generated
- Reports can be generated
- Level 1, Level 2, and Level 3 autonomy rules are enforced
- All Hermes tool actions are logged
- Skills can be executed and reused

---

# 25. Key Technical Risks

## Hermes Integration Risk

Risk:

Hermes may not expose every integration primitive needed for STRATOS.

Mitigation:

Use a backend Hermes Gateway to normalize interaction and isolate STRATOS from Hermes internals.

## Skill Generation Risk

Risk:

Automatic skill creation may be unreliable.

Mitigation:

Treat learned skill generation as experimental in MVP.

## Data Cleaning Risk

Risk:

Incorrect cleaning may distort scientific interpretation.

Mitigation:

Always preserve raw data, show cleaning methods, provide before and after comparisons, and require human review for research conclusions.

## Shell Access Risk

Risk:

Terminal access can modify or damage system state.

Mitigation:

Require Level 3 approval, sandbox execution, log commands, and restrict production credentials.

## Knowledge Retrieval Risk

Risk:

Hermes may retrieve outdated or irrelevant documents.

Mitigation:

Store metadata, show citations, rank by recency and relevance, and allow users to inspect sources.

---

# 26. Open Technical Questions

1. Which vector database will be used for MVP?
2. Will SharePoint ingestion use Microsoft Graph API or manual file export first?
3. Will Hermes run locally, on a VPS, or inside the backend environment?
4. What map library will the frontend use?
5. What exact telemetry format will LIFTS standardize around?
6. What permission system will be used for team roles?
7. How will shell command execution be sandboxed?
8. What file formats must the data cleaning pipeline support first?
9. How will Hermes-created skills be exported, backed up, or versioned?
10. What deployment target will be used for the first demo?

---

# 27. Recommended MVP Defaults

If no decision has been made, use these defaults:

- Frontend: Next.js
- Backend: FastAPI
- Database: Supabase PostgreSQL
- Vector DB: Supabase Vector
- File Storage: Supabase Storage
- Map UI: Leaflet
- Charts: Recharts
- Data Processing: Python pandas, scipy, numpy
- Background Jobs: Celery or FastAPI background tasks
- Hermes Hosting: VPS
- SharePoint Ingestion: Manual export first, Microsoft Graph later
- Obsidian Ingestion: Local vault folder sync
- Telemetry Format: CSV and JSON first

---

# 28. Final Technical Positioning

STRATOS should be engineered as a reliable mission operations platform first and an agent-assisted intelligence system second.

The deterministic backend owns mission state, telemetry, artifacts, and permissions.

Hermes owns natural language interaction, workflow automation, knowledge retrieval, skill creation, and analysis assistance.

This separation allows STRATOS to remain operationally reliable while still benefiting from self-improving agent capabilities.
