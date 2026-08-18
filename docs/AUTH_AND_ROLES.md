# Authentication & Role-Based Access Control

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Backend (FastAPI, middleware), Frontend (login flow), DevOps (Supabase config)

---

## Overview

STRATOS uses **Supabase Auth** for user authentication (email/password), backed by PostgreSQL. Role-based access control (RBAC) gates operations on missions and flights.

**Flow**: User logs in → Supabase issues JWT → Frontend stores token → Requests include Bearer token → STRATOS validates + checks role

---

## Authentication (Supabase)

### Supabase Setup

Supabase config already exists in repo (`supabase/`). Key tables:

```sql
-- Supabase-managed (auth.users)
-- email, password, created_at, last_sign_in_at

-- STRATOS-managed
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email VARCHAR UNIQUE NOT NULL,
  full_name VARCHAR,
  avatar_url VARCHAR,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES public.users(id),
  mission_id UUID REFERENCES public.missions(id),
  role VARCHAR NOT NULL, -- Captain, Co-Captain, Chief_Engineer, Team_Member, Observer
  auth_level VARCHAR NOT NULL, -- full_control, edit, view_only
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, mission_id)
);
```

### Login Flow

1. **Frontend**: User enters email/password → calls Supabase `signUp()` or `signIn()`
2. **Supabase**: Authenticates against `auth.users` table
3. **Supabase Response**: Returns `{ user, session: { access_token, refresh_token } }`
4. **Frontend**: Stores token in localStorage or secure cookie
5. **Subsequent Requests**: Header `Authorization: Bearer <access_token>`

### Token Structure

**JWT** (Supabase-issued):
```
{
  "sub": "user_uuid",
  "email": "user@uprm.edu",
  "email_verified": true,
  "aud": "authenticated",
  "iat": 1700000000,
  "exp": 1700003600,
  "iss": "https://xyzabc.supabase.co"
}
```

**Expiry**: 1 hour  
**Refresh**: Use `refresh_token` to get new `access_token`

---

## Role-Based Access Control (RBAC)

### Roles

Defined per mission. User can have different roles in different missions.

| Role | Authority | Typical Use |
|------|-----------|------------|
| **Captain** | Full mission control; approves launches; manages team | Mission lead |
| **Co-Captain** | Approves launches; acts for Captain; manages payload | Deputy lead |
| **Chief_Engineer** | Approves launches; manages technical decisions | PMSE, PDM, RDA, PMAD leads |
| **Team_Member** | Chat, views mission state, executes skills | Team members |
| **Observer** | Read-only; can chat but cannot modify | Advisors, mentors |

### Authorization Levels

Scoped per mission + operation:

| Level | Operations |
|-------|-----------|
| **full_control** | Create/read/update/delete missions, flights, payloads, approve launches, manage team |
| **edit** | Read/update missions, flights, payloads; cannot approve launches or manage team |
| **view_only** | Read missions, flights, telemetry; cannot modify anything |

### Mapping: Role → Auth Level

| Role | Default Auth Level |
|------|-------------------|
| Captain | full_control |
| Co-Captain | full_control |
| Chief_Engineer | edit |
| Team_Member | edit |
| Observer | view_only |

---

## Permission Matrix

### Mission Operations

| Operation | Captain | Co-Captain | Chief_Eng | Team_Member | Observer |
|-----------|---------|-----------|----------|----------|----------|
| Create mission | ✓ | ✗ | ✗ | ✗ | ✗ |
| Edit mission (name, desc) | ✓ | ✓ | ✓ | ✗ | ✗ |
| Delete mission | ✓ | ✗ | ✗ | ✗ | ✗ |
| View mission | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manage team (add/remove) | ✓ | ✓ | ✗ | ✗ | ✗ |

### Flight Operations

| Operation | Captain | Co-Captain | Chief_Eng | Team_Member | Observer |
|-----------|---------|-----------|----------|----------|----------|
| Create flight | ✓ | ✓ | ✓ | ✗ | ✗ |
| Edit flight (launch window, payload) | ✓ | ✓ | ✓ | ✗ | ✗ |
| Delete flight (Preparing only) | ✓ | ✓ | ✗ | ✗ | ✗ |
| Approve launch (gate) | ✓ | ✓ | ✓ | ✗ | ✗ |
| View telemetry | ✓ | ✓ | ✓ | ✓ | ✓ |
| Execute skill | ✓ | ✓ | ✓ | ✓ | ✗ |

### Chat

| Operation | Captain | Co-Captain | Chief_Eng | Team_Member | Observer |
|-----------|---------|-----------|----------|----------|----------|
| Send message | ✓ | ✓ | ✓ | ✓ | ✓ |
| Call tools | ✓ | ✓ | ✓ | ✓ | ✗ |
| View chat history | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Implementation (FastAPI Middleware)

### JWT Validation Middleware

```python
# backend/auth.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from supabase import create_client

security = HTTPBearer()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(mission_id: str, required_role: str):
    async def check_role(user = Depends(get_current_user)):
        # Query user_roles table for this mission
        role = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.mission_id == mission_id
        ).first()
        
        if not role or role.role not in required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return role
    
    return check_role
```

### Endpoint Protection

```python
@app.post("/missions/{mission_id}/flights")
async def create_flight(
    mission_id: str,
    flight: FlightCreate,
    role = Depends(require_role(mission_id, ["Captain", "Co-Captain", "Chief_Engineer"]))
):
    # Only Captain/Co-Captain/Chief_Eng can create flights
    ...
```

---

## Special Cases

### System Roles (Admin)

Superusers can manage any mission (bypass RBAC). Identified by `user_roles.role = "System_Admin"`.

```python
async def is_admin(user = Depends(get_current_user)):
    admin = db.query(User).filter(User.id == user.id, User.is_admin == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin
```

### Launch Approval (Multi-Sig)

Launch requires **at least 2 approvals** from {Captain, Co-Captain, Chief_Engineer}.

```python
@app.post("/flights/{flight_id}/approval")
async def submit_approval(flight_id: str, approval: ApprovalCreate, user = Depends(get_current_user)):
    # Check user has launch approval authority
    role = check_mission_role(flight_id, user.id)
    if role.role not in ["Captain", "Co-Captain", "Chief_Engineer"]:
        raise HTTPException(status_code=403, detail="Cannot approve launches")
    
    # Add approval
    db.create(Approval, flight_id=flight_id, approved_by=user.id, ...)
    
    # Check if 2+ approvals; if so, send notification
    approvals = db.query(Approval).filter(Approval.flight_id == flight_id).all()
    if len(approvals) >= 2:
        notify_external_approval_system(flight_id)
```

---

## Token Refresh

```python
@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    try:
        new_session = supabase.auth.refresh_session(refresh_token)
        return {
            "access_token": new_session.session.access_token,
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Refresh failed")
```

---

## Logout

```python
@app.post("/auth/logout")
async def logout(user = Depends(get_current_user)):
    supabase.auth.sign_out()
    # Frontend clears token from localStorage
    return {"success": True}
```

---

## Testing

### Mock User Setup

```python
# tests/conftest.py
@pytest.fixture
def authorized_user():
    return {
        "id": "user_123",
        "email": "captain@lifts.uprm.edu",
        "roles": [{"mission_id": "mission_001", "role": "Captain"}]
    }
```

---

## Next: Implement Supabase schema migrations

- `supabase/migrations/001_create_users.sql`
- `supabase/migrations/002_create_user_roles.sql`
