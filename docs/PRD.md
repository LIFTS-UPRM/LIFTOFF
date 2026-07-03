# STRATOS Product Requirements Document (PRD)

## Version

v1.0

## Product Name

STRATOS

---

# Vision

STRATOS is an agent-assisted mission operations platform for LIFTS that unifies mission planning, flight operations, telemetry monitoring, post-flight scientific analysis, and institutional knowledge management through Hermes.

By combining operational tools, organizational knowledge, telemetry data, and autonomous workflows, STRATOS becomes a persistent mission operator that learns how LIFTS conducts missions and continuously improves operational efficiency over time.

---

# Problem Statement

High-altitude balloon missions involve multiple disconnected workflows across planning, operations, recovery, analysis, and documentation.

Mission teams frequently switch between:

- Documentation systems
- Checklists
- Prediction tools
- Telemetry dashboards
- Data analysis software
- Historical mission reports

This fragmentation creates inefficiencies, knowledge loss between semesters, and inconsistent operational procedures.

LIFTS requires a centralized platform that preserves institutional knowledge while supporting the complete mission lifecycle.

---

# Product Goals

## Mission Lifecycle Management

Provide a unified platform for pre-flight, flight, and post-flight operations.

## Institutional Knowledge Preservation

Allow Hermes to learn organizational procedures and make historical knowledge accessible to future team members.

## Operational Automation

Reduce repetitive mission tasks through reusable skills and workflow automation.

## Scientific Data Processing

Enable automated telemetry cleaning, analysis, and interpretation for research use.

## Team Onboarding

Allow new members to learn procedures, mission history, and best practices directly from Hermes.

---

# Target Users

## Primary Users

- LIFTS Student Team Members

## Secondary Users

- Team Leads
- Mission Directors
- Payload Engineers
- Data Analysis Teams
- New Team Members

## Expected Team Size

- 5-20 users per mission

---

# Core Architecture

STRATOS consists of four primary layers.

## 1. Experience Layer

User-facing systems.

Components:

- Web Application
- Mission Dashboard
- Telemetry Dashboard
- Checklist Interface
- Artifact Renderer
- Analytics Interface

---

## 2. Hermes Intelligence Layer

Hermes serves as the intelligence layer of STRATOS.

Responsibilities:

- Natural language interaction
- Knowledge retrieval
- Tool orchestration
- Workflow execution
- Skill management
- Team onboarding
- Mission assistance
- Data interpretation

Hermes operates across all phases of the mission lifecycle.

---

## 3. Operational Layer

Mission-specific systems.

Components:

- Mission Management
- Checklist System
- Telemetry Pipeline
- Prediction Services
- Data Cleaning Engine
- Analysis Engine
- Reporting Engine

---

## 4. Knowledge Layer

Institutional knowledge systems.

Components:

- Obsidian Vault
- SharePoint
- Mission History
- Flight Reports
- Historical Discussions
- Vector Database
- Mission Database

---

# Product Pillars

## 1. Pre-Flight Operations

### Purpose

Prepare missions efficiently and consistently.

### Features

- Mission creation
- Mission planning
- Mission documentation
- Dynamic checklists
- Launch readiness review
- Document management
- Historical mission lookup

### Hermes Capabilities

- Generate checklists
- Explain procedures
- Answer operational questions
- Retrieve documentation
- Assist new members
- Recommend readiness actions

---

## 2. Flight Operations

### Purpose

Provide real-time mission awareness.

### Features

- Live telemetry monitoring
- Mission status tracking
- Trajectory visualization
- Prediction overlays
- Operational alerts

### Hermes Capabilities

- Query telemetry
- Explain anomalies
- Summarize mission status
- Generate operational reports
- Execute prediction workflows

---

## 3. Post-Flight Operations

### Purpose

Transform raw telemetry into scientifically useful datasets.

### Features

- Telemetry ingestion
- Dataset validation
- Data cleaning
- Data visualization
- Scientific reporting
- Mission review workflows

### Hermes Capabilities

- Identify sensor anomalies
- Detect missing values
- Remove outliers
- Correct timestamps
- Apply interpolation methods
- Recommend cleaning approaches
- Generate plots
- Explain results
- Compare flights
- Produce mission reports

---

# Institutional Knowledge Layer

Hermes retrieves long-term operational knowledge for LIFTS. The underlying
sources, not the model, remain the authority for that knowledge.

Knowledge Sources:

- Obsidian Vault
- SharePoint Documents
- Mission Reports
- Flight Logs
- Team Procedures
- Historical Discussions
- Telemetry Analysis Results

Hermes should be capable of teaching new members how LIFTS operates using accumulated organizational knowledge.

---

# Memory Architecture

STRATOS uses a hybrid memory architecture.

## Structured Memory

Relational Database

Stores:

- Missions
- Users
- Checklists
- Telemetry
- Artifacts
- Mission Metadata
- Skill Metadata

---

## Semantic Memory

Vector Database

Stores:

- Documentation
- Mission Reports
- Historical Knowledge
- Operational Procedures
- Lessons Learned
- Analysis Summaries

This architecture enables Hermes to retrieve factual information from databases while accessing institutional knowledge through semantic search.

---

# Knowledge Ingestion Pipeline

## Sources

- Obsidian
- SharePoint

## Pipeline

Documents → Parsing → Metadata Extraction → Chunking → Embedding → Vector Storage

## Metadata

- Source
- Author
- Date
- Project
- Document Type

Hermes must provide source attribution when referencing retrieved information.

---

# Skills System

A skill is a reusable operational capability managed by Hermes.

Skills consist of:

- Goal
- Context
- Required Inputs
- Execution Logic
- Tool Calls
- Memory References
- Expected Outputs

## Example Skills

- PredictTrajectory
- RecoveryPlanner
- TelemetryAnalyzer
- LaunchReadinessReview
- PostFlightReportGenerator
- DataCleaningWorkflow

Skills generated by Hermes remain proprietary to LIFTS.

---

# Skill Lifecycle

## Explicit Creation

User:

"Create a skill for launch readiness reviews."

Hermes generates and stores the skill.

---

## Learned Creation

Hermes observes recurring workflows and proposes reusable skills.

Example:

```text
Run trajectory prediction
Analyze landing zone
Generate recovery report
```

Repeated execution may produce:

```text
Recovery Planning Skill
```

Skill generation is considered an experimental MVP capability.

---

# Artifact System

Hermes determines the most appropriate artifact based on user intent.

Supported Artifacts:

- Maps
- Tables
- Charts
- Reports
- Checklists
- Timelines
- Alerts

Artifacts should be interactive whenever possible.

## Map Artifact

Supports:

- Zoom
- Layer selection
- Marker interaction
- Telemetry filtering

## Chart Artifact

Supports:

- Data filtering
- Comparison modes
- Zooming
- Historical overlays

---

# Tool Execution Model

Hermes can execute operational tools.

Examples:

- Trajectory prediction
- Telemetry analysis
- Mission queries
- Data processing
- Report generation

## External Integrations

Future integrations include:

- APRS
- NOAA
- Radiosonde Systems
- Custom LIFTS Tools

---

# Autonomy Model

## Level 1: Read Operations

No approval required.

Examples:

- Read telemetry
- Query missions
- Generate reports
- Retrieve documentation

---

## Level 2: Operational Changes

Execute first.

Notify user.

Offer undo.

Examples:

- Update mission fields
- Create artifacts
- Create skills
- Modify checklists

---

## Level 3: Administrative/System Actions

Explicit approval required.

Examples:

- Shell commands
- Code execution
- System modifications
- Mission deletion

Administrative actions require authorization.

---

# MVP Scope

## Included

- Mission management
- Dynamic checklists
- Live telemetry monitoring
- Telemetry storage
- Mission visualization
- Hermes chat interface
- Obsidian integration
- SharePoint integration
- Vector search
- Skill execution
- Experimental skill generation
- Trajectory prediction workflows
- Data cleaning
- Scientific analysis
- Report generation
- Interactive artifacts

## Excluded

- Multi-organization support
- Public skill marketplace
- Autonomous mission execution
- Large-scale fleet management
- Production-grade deployment infrastructure

---

# Non-Goals

STRATOS is not intended to:

- Replace flight safety procedures
- Autonomously launch missions
- Make safety-critical decisions without human review
- Replace scientific judgment
- Serve multiple organizations during the MVP phase

---

# Success Metrics & KPIs

## Mission Operations Metrics

### Mission Preparation Time

Target:

- Reduce mission preparation time by 30%

### Checklist Completion Efficiency

Target:

- Reduce checklist completion time by 25%

### Operational Query Resolution

Target:

- Hermes responds to common operational questions within 10 seconds

---

## Knowledge Management Metrics

### Knowledge Retrieval Success Rate

Target:

- 90%+ successful retrieval of relevant documents

### New Member Onboarding

Target:

- Reduce onboarding time by 50%

### Historical Knowledge Coverage

Target:

- 100% of archived mission reports indexed and retrievable

---

## Flight Operations Metrics

### Telemetry Availability

Target:

- Greater than 99% telemetry availability

### Prediction Workflow Time

Target:

- Less than 30 seconds from request to artifact generation

### Mission Status Awareness

Target:

- Accurate mission summaries generated from telemetry and mission data

---

## Post-Flight Analysis Metrics

### Data Cleaning Time

Current State:

- Manual processing by team members

Target:

- Reduce processing time by 80%

### Report Generation Time

Target:

- Generate complete mission reports in under 5 minutes

### Data Quality Improvement

Target:

- Detect and correct 95% of common telemetry anomalies

---

## Skill System Metrics

### Skill Reuse Rate

Target:

- At least 50% of generated skills reused

### Workflow Automation Coverage

Target:

- Assist or automate 60% of repetitive mission workflows

### Skill Generation Accuracy

Target:

- Greater than 80% acceptance of proposed skills

---

## Institutional Knowledge Metrics

### Historical Mission Utilization

Target:

- Historical mission context referenced during planning and analysis workflows

### Knowledge Preservation

Target:

- Critical procedures and lessons learned remain accessible across academic years

---

# North Star Metric

## Mission Operational Autonomy Score (MOAS)

Definition:

(Number of mission tasks completed with Hermes assistance)

÷

(Total mission tasks performed)

Goal:

- Achieve 70% assisted mission operations within the first academic year

---

# Definition of Done

The MVP is complete when:

- Missions can be created and managed
- Checklists can be generated and updated
- Telemetry can be ingested and visualized
- Hermes can access organizational knowledge
- Hermes can execute mission workflows
- Trajectory prediction workflows function correctly
- Telemetry data can be cleaned automatically
- Analysis reports can be generated
- Interactive artifacts are rendered correctly
- New members can retrieve historical knowledge through Hermes
- Skills can be created and reused

---

# Long-Term Vision

STRATOS becomes the operational memory and intelligence system of LIFTS.

As members graduate and new students join, operational knowledge, mission experience, data analysis techniques, successful workflows, and mission history remain accessible through Hermes.

The system evolves from an assistant into a persistent institutional expert capable of preserving, amplifying, and operationalizing the collective knowledge of the organization while supporting the complete aerospace mission lifecycle.
