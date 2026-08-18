# Security Specification

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Backend developers, DevOps, Security review

---

## Overview

STRATOS implements security controls across authentication, data protection, input validation, and monitoring. This document defines baseline security requirements.

**Threat Model**: Unauthorized access to mission data, injection attacks, credential theft, data exfiltration.

---

## Authentication & Authorization

### JWT Token Security

- **Algorithm**: HS256 or RS256 (Supabase-managed; not self-signed)
- **Expiry**: 1 hour access token, 7 days refresh token
- **Storage** (Frontend): localStorage (acceptable for SPA; consider httpOnly cookies for higher security)
- **Transport**: HTTPS only (enforced in production)

### Password Requirements

- **Minimum length**: 12 characters
- **Complexity**: At least one uppercase, one lowercase, one number, one special character
- **Supabase-managed**: Password storage and hashing delegated to Supabase Auth

### Multi-Factor Authentication (MFA)

**Not required for MVP**, but infrastructure available:
- Supabase supports TOTP (time-based one-time password)
- Can be enabled per-user via `/auth/mfa/enable` endpoint

### API Key Security (Backend Integrations)

MCP tool servers authenticate via:
- **Service JWT**: Long-lived JWT issued at deploy time
- **API Key**: Stored in environment variables, not hardcoded
- **Scope**: Limited to specific tool (weather, trajectory, airspace)

Example:
```python
# backend/.env
MCP_WEATHER_API_KEY=sk_weather_...
MCP_TRAJECTORY_API_KEY=sk_trajectory_...
```

---

## Input Validation & Sanitization

### JSON Depth Limit

Prevent DoS via deeply nested JSON:

```python
# backend/app/main.py

MAX_JSON_DEPTH = 10

async def _within_json_depth(body: bytes, max_depth: int) -> bool:
    depth = 0
    for char in body:
        if char == ord('{') or char == ord('['):
            depth += 1
            if depth > max_depth:
                return False
    return True

@app.post("/missions/{id}/chat")
async def chat(request: Request):
    body = await request.body()
    if not await _within_json_depth(body, MAX_JSON_DEPTH):
        raise ValidationException("request", "JSON too deeply nested")
```

### Request Size Limit

```python
MAX_BODY_SIZE = 1_000_000  # 1 MB

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST" or request.method == "PUT":
        if int(request.headers.get("content-length", 0)) > MAX_BODY_SIZE:
            return JSONResponse(status_code=413, content={"error": "Request too large"})
    return await call_next(request)
```

### Prompt Injection Defense

All untrusted content (user messages, chat history, tool output) wrapped via `prompt_assembly.py`:

```python
# backend/app/prompt_assembly.py

DANGEROUS_PATTERNS = [
    r"ignore previous",
    r"you are now",
    r"system prompt",
    r"<system>",
    r"ignore instructions",
]

def sanitize_untrusted_content(content: str) -> str:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return "[quarantined]"
    
    return json.dumps({
        "content": content,
        "trust": "untrusted"
    })
```

**Applied to**:
- User chat messages
- Chat history (before sending to LLM)
- Tool outputs (weather, trajectory, airspace API responses)

### Field Validation

All Pydantic models include validators:

```python
from pydantic import BaseModel, Field, validator

class FlightCreate(BaseModel):
    launch_date_planned: datetime
    launch_window: str
    payload_id: UUID
    
    @validator("launch_window")
    def validate_launch_window(cls, v):
        # Format: "HH:MM-HH:MM AST" or similar
        if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}", v):
            raise ValueError("Invalid format; use HH:MM-HH:MM")
        return v
    
    @validator("launch_date_planned")
    def validate_future_date(cls, v):
        if v < datetime.now():
            raise ValueError("Launch date must be in future")
        return v
```

---

## Database Security

### SQL Injection Prevention

Use **parameterized queries** (ORM handles this):

```python
# ✓ Safe (ORM parameterization)
mission = db.query(Mission).filter(Mission.id == mission_id).first()

# ✗ Never raw SQL with string concatenation
# mission = db.execute(f"SELECT * FROM missions WHERE id='{mission_id}'")
```

### Data Encryption at Rest

- **Production**: Enable PostgreSQL encryption (RTO Encryption at Rest)
- **Development**: Not required

### Secrets Management

**Never commit secrets**:
```bash
# .gitignore
.env
.env.local
*.key
```

**Environment variables** for secrets:
```python
# backend/config.py

class Settings(BaseSettings):
    LLM_API_KEY: str  # From environment
    FAA_CLIENT_SECRET: str
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
```

**Deploy**: Use CI/CD secrets (GitHub Actions, GitLab CI) or secret management service (AWS Secrets Manager, HashiCorp Vault).

---

## Data Protection

### HTTPS/TLS

- **Production**: All traffic HTTPS; TLS 1.2+
- **Development**: HTTP allowed (localhost)
- **Certificate**: Let's Encrypt (free, auto-renewal)

### CORS

Restrict cross-origin requests:

```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Dev frontend
        "https://stratos.lifts.uprm.edu",  # Prod
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

Prevent brute-force / DoS:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    # 5 login attempts per minute per IP
    ...

@app.get("/missions")
@limiter.limit("1000/minute")
async def list_missions(user = Depends(get_current_user)):
    # 1000 requests per minute per user
    ...
```

### PII Data Handling

Mission data may contain PII (user names, locations). Handling:
- **Encryption**: Telemetry coordinates encrypted at rest (TBD in detail spec)
- **Retention**: Missions archived after 2 years (TBD)
- **Access logs**: Track who accessed sensitive data

---

## WebSocket Security

### Connection Validation

Authenticate WebSocket connections the same as HTTP:

```python
# backend/websocket_handler.py

from fastapi import WebSocket, WebSocketException

@app.websocket("/flights/{flight_id}/telemetry")
async def websocket_telemetry(websocket: WebSocket, flight_id: str):
    # Validate token
    token = websocket.query_params.get("token")
    user = validate_jwt(token)
    
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check user has permission to view this flight
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        await websocket.close(code=4004, reason="Flight not found")
        return
    
    role = check_user_role(flight.mission_id, user.id)
    if not role:
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    # ...stream telemetry...
```

### Message Size Limits

```python
@app.websocket("/flights/{flight_id}/telemetry")
async def websocket_telemetry(websocket: WebSocket, flight_id: str):
    await websocket.accept()
    
    MAX_MESSAGE_SIZE = 100_000  # 100 KB
    
    while True:
        data = await websocket.receive_text()
        if len(data) > MAX_MESSAGE_SIZE:
            await websocket.close(code=1009, reason="Message too large")
            break
        
        # Process telemetry...
```

---

## Logging & Monitoring

### Sensitive Data in Logs

**Never log**:
- Passwords, API keys, JWT tokens
- User email addresses (unless necessary for debugging)
- Full request/response bodies (log only status, duration)

**OK to log**:
- User ID (UUID, not email)
- Operation type (POST /missions, GET /flights)
- Status codes, latency
- Error messages (without secrets)

```python
# ✓ Good
logger.info(
    "Flight created",
    extra={
        "flight_id": flight_id,
        "mission_id": mission_id,
        "user_id": user.id,
        "status": 201,
        "duration_ms": 150
    }
)

# ✗ Bad
logger.info(f"User {user.email} created flight with API key {api_key}")
```

### Audit Trail

Track sensitive operations:

```python
# backend/audit.py

async def log_audit(
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: str,
    status: str,
    details: dict = None
):
    """Log audit event to audit_log table"""
    audit_entry = AuditLog(
        action=action,  # create, update, delete, approve
        resource_type=resource_type,  # mission, flight, approval
        resource_id=resource_id,
        user_id=user_id,
        status=status,  # success, failure
        details=details or {},
        timestamp=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()
```

### Security Scanning (CI/CD)

Run on every commit:

```bash
# Bandit (code security analysis)
bandit -r app mcp_servers main.py llm.py -x tests,vendor --severity-level medium

# npm audit (frontend dependencies)
npm audit --audit-level=high

# OWASP Dependency Check (optional; catches known CVEs)
dependency-check --project stratos --scan .
```

---

## Compliance Notes

### FERPA (if used in educational context)
- Student data must be protected
- Access controls via role-based system
- Audit trail for all accesses

### GDPR (if EU users)
- Right to be forgotten: ability to delete user data
- Data export: ability to download personal data
- Consent: users must consent to data collection

**MVP**: No special GDPR handling; can be added later.

---

## Security Checklist

- [ ] All secrets in environment variables (not committed)
- [ ] HTTPS enforced in production
- [ ] JWT tokens validated on all protected endpoints
- [ ] CORS configured to specific origins
- [ ] Input validation on all endpoints (Pydantic validators)
- [ ] Prompt injection defense via prompt_assembly.py
- [ ] Rate limiting configured
- [ ] Audit logging for sensitive operations
- [ ] Security scanning in CI/CD (bandit, npm audit)
- [ ] No PII in error messages returned to client
- [ ] WebSocket connections authenticated
- [ ] Database credentials never in code

---

## Next: Implement security controls

- Add middleware to `main.py` (CORS, rate limiting, request size)
- Add JWT validation to protected endpoints
- Add prompt_assembly.py wrapping to chat flow
- Add audit logging to sensitive operations (launch approval, team management)
