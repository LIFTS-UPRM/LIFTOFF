# Skills System

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Backend developers (skill definitions), Mission planners (skill usage)

---

## Overview

Skills are reusable workflows and checklists for mission operations. STRATOS ships with core skills (version-controlled), and teams can create custom skills (database-stored).

**Purpose**: Automate routine mission tasks (preflight checklist, launch readiness review, recovery procedures).

**Model**: Hybrid (code + database).

---

## Core Skills (Code-Defined)

**Location**: `backend/skills/`

**Examples**:
1. **Pre-Launch Payload Checklist** (template)
   - GPS powered? ✓
   - Temperature sensor active? ✓
   - Battery voltage >4.5V? ✓
   - Radio link established? ✓

2. **Launch Readiness Review** (interactive workflow)
   - Copilot asks: "Is weather within launch criteria?"
   - User responds → copilot suggests next question
   - Guides user to approval decision

3. **Recovery Checklist** (template)
   - Payload located? ✓
   - GPS coordinates recorded? ✓
   - Sensors shut down? ✓
   - Photos/log taken? ✓

### Skill Definition (Python/YAML)

```yaml
# backend/skills/preflight_checklist.yaml

id: preflight_checklist
type: checklist_template
name: "Pre-Launch Payload Checklist"
description: "Verify payload systems before launch"

fields:
  - name: gps_powered
    label: "GPS powered and transmitting?"
    type: checkbox
    required: true
    help: "Check ground station receiver shows GPS fix"
  
  - name: temperature_sensor
    label: "Temperature sensor active?"
    type: checkbox
    required: true
    help: "Verify via debug log or test read"
  
  - name: battery_voltage
    label: "Battery voltage (V):"
    type: number
    required: true
    min: 4.5
    max: 5.0
    help: "Should be 4.5V or higher"
  
  - name: radio_link
    label: "Radio link established?"
    type: checkbox
    required: true
    help: "Confirm signal on ground station"

on_complete:
  - log_execution
  - notify_team: "Preflight checklist complete"
```

### Core Skills Registry

```python
# backend/skills/__init__.py

CORE_SKILLS = {
    "preflight_checklist": SkillDefinition.from_yaml("preflight_checklist.yaml"),
    "launch_readiness_review": SkillDefinition.from_yaml("launch_readiness_review.yaml"),
    "recovery_checklist": SkillDefinition.from_yaml("recovery_checklist.yaml"),
}
```

---

## Custom Skills (Database-Stored)

**Table**: `skills`

```sql
CREATE TABLE public.skills (
  id UUID PRIMARY KEY,
  mission_id UUID REFERENCES public.missions(id),
  type VARCHAR, -- interactive_workflow, checklist_template
  name VARCHAR NOT NULL,
  description TEXT,
  definition JSONB, -- Skill structure (steps, fields, etc.)
  created_by UUID REFERENCES public.users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Custom Skill Definition

Teams can create skills via API. Example:

```json
POST /missions/mission_001/skills

{
  "type": "checklist_template",
  "name": "SCRAM Payload Assembly",
  "description": "Solar cell panel assembly verification",
  "fields": [
    {
      "name": "panel_alignment",
      "label": "Solar panels aligned to sun?",
      "type": "checkbox"
    },
    {
      "name": "connector_voltage",
      "label": "Connector voltage (V):",
      "type": "number",
      "min": 4.0,
      "max": 5.5
    }
  ]
}
```

---

## Skill Execution

### API Endpoint

```
POST /missions/{mission_id}/skills/{skill_id}/execute
```

**Request**:
```json
{
  "flight_id": "flight_001",
  "responses": {
    "gps_powered": true,
    "temperature_sensor": true,
    "battery_voltage": 4.8,
    "radio_link": true
  }
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_001",
    "skill_id": "preflight_checklist",
    "status": "completed",
    "results": {
      "all_checks_passed": true,
      "timestamp": "2026-07-27T14:30:00Z",
      "executed_by": "user_123"
    }
  }
}
```

### Checklist Execution

1. Frontend renders form with fields from skill definition
2. User fills in checkbox/text/number inputs
3. User clicks "Submit"
4. POST to `/skills/{skill_id}/execute`
5. Backend validates required fields
6. Backend saves execution record
7. Backend triggers `on_complete` actions (logging, notifications)

### Interactive Workflow Execution

1. Copilot initiates skill: "Let's walk through Launch Readiness Review. Ready?"
2. User: "Yes"
3. Copilot asks step 1: "Is weather within launch criteria?"
4. User: "Yes, forecast shows clear skies and favorable winds"
5. Copilot stores response, asks step 2
6. ...continues until skill completes
7. Copilot: "Review complete. Recommend proceeding with launch approval."

**Implementation**: Chat API recognizes skill ID in context; routes copilot through skill steps.

---

## Skill Execution History

**Table**: `skill_executions`

```sql
CREATE TABLE public.skill_executions (
  id UUID PRIMARY KEY,
  mission_id UUID,
  flight_id UUID,
  skill_id UUID,
  user_id UUID REFERENCES public.users(id),
  execution_data JSONB, -- Responses/results
  status VARCHAR, -- completed, failed, in_progress
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Query**: List all skill executions for a flight
```
GET /flights/{flight_id}/skill_executions
```

---

## Integration with Chat

### Skill Invocation from Chat

User asks copilot: "Run the preflight checklist for me"

Copilot detects skill request → routes to skill engine:

```python
# backend/chat flow

if "checklist" in user_message.lower():
    # Find matching skill
    skill = find_skill_by_name(mission_id, "preflight_checklist")
    
    if skill and skill.type == "checklist_template":
        # Return skill form to frontend
        return {
            "response": "Let's verify payload systems...",
            "skill_form": skill.definition
        }
    
    elif skill and skill.type == "interactive_workflow":
        # Start workflow; copilot guides steps
        return {
            "response": "Ready to walk through Launch Readiness Review?",
            "next_step": skill.steps[0]
        }
```

---

## Deployment

### Core Skills

Core skills ship with code:
```bash
backend/
├── skills/
│   ├── __init__.py
│   ├── preflight_checklist.yaml
│   ├── launch_readiness_review.yaml
│   └── recovery_checklist.yaml
```

Add new core skill → commit to repo → deploy.

### Custom Skills

Custom skills created via API → stored in database → available immediately (no deploy).

---

## Versioning

**Core Skills**: Follow app version (e.g., v1.0.0 includes Checklist v1)

**Custom Skills**: Immutable execution history; changes create new skill (old version preserved)

```python
# Update skill → increment version
{
  "id": "skill_001_v1",  # original
  "name": "SCRAM Payload Assembly"
}
# User modifies
{
  "id": "skill_001_v2",  # new version
  "name": "SCRAM Payload Assembly v2"
}
```

---

## Validation

### Checklist Validation

- Required fields must be filled
- Number fields must be within min/max range
- No extra fields allowed

### Workflow Validation

- User response must match expected input type
- Copilot can re-ask if response unclear

---

## Testing

### Mock Skill

```python
# tests/test_skills.py

@pytest.fixture
def mock_preflight_skill():
    return {
        "id": "preflight_checklist",
        "type": "checklist_template",
        "fields": [
            {"name": "gps_powered", "type": "checkbox"}
        ]
    }
```

---

## Next: Implement skill CRUD + execution endpoints

- `skills.py`: GET, POST skill endpoints
- `skill_executor.py`: Checklist + workflow validation
- Chat integration: detect skill requests, route to executor
