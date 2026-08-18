# Error Handling Patterns

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Backend developers (implementation), Frontend developers (consumption)

---

## Overview

STRATOS uses consistent error responses across all API endpoints. Errors are categorized by type (auth, validation, state, external tool failure) and include actionable messages for frontend.

**Goal**: Every error response tells the user/developer what went wrong and how to recover.

---

## Response Format

### Success (2xx)

```json
{
  "success": true,
  "data": { /* entity or list */ },
  "error": null,
  "timestamp": "2026-07-22T13:00:00Z"
}
```

### Error (4xx, 5xx)

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "status": 400,
    "details": { /* optional additional context */ }
  },
  "timestamp": "2026-07-22T13:00:00Z"
}
```

---

## Error Codes & Status Codes

### Authentication & Authorization

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `AUTH_INVALID` | 401 | Invalid or expired token | Refresh token; re-login if refresh fails |
| `AUTH_REQUIRED` | 401 | Missing Authorization header | Include Bearer token in header |
| `AUTH_PROVIDER_ERROR` | 500 | Supabase auth service error | Retry; contact admin if persistent |
| `PERMISSION_DENIED` | 403 | User lacks role for operation | Escalate request to Captain/Co-Captain |

### Validation

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `VALIDATION_ERROR` | 400 | Invalid request body | Check request format against API spec |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing (e.g., "name") | Include all required fields |
| `INVALID_FIELD_TYPE` | 400 | Field type mismatch (e.g., string instead of number) | Correct field type |
| `INVALID_ENUM` | 400 | Invalid enum value (e.g., state must be Planning\|Ready) | Use allowed values |

### Resource Not Found

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `MISSION_NOT_FOUND` | 404 | Mission with ID xyz not found | Verify mission ID; fetch mission list |
| `FLIGHT_NOT_FOUND` | 404 | Flight with ID xyz not found | Verify flight ID; fetch flight list |
| `USER_NOT_FOUND` | 404 | User not found in this mission | Verify user exists; add to team if needed |

### State Conflict

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `STATE_INVALID_TRANSITION` | 409 | Cannot transition from Preparing to Analyzed | Follow correct state sequence (Preparing→Armed→Launched→In Flight→Recovered→Analyzed) |
| `FLIGHT_ACTIVE` | 409 | Cannot modify flight while In Flight | Wait for flight to transition to Recovered |
| `APPROVAL_REQUIRED` | 409 | Launch requires approval from Captain/Co-Captain | Obtain launch approval before proceeding |
| `DUPLICATE_ENTRY` | 409 | User already in mission team | Use different user or remove existing entry |

### External Tool Failures

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `WEATHER_TOOL_ERROR` | 503 | Weather service unreachable | Retry; use cached weather if available |
| `TRAJECTORY_TOOL_ERROR` | 503 | Trajectory prediction failed | Retry with different launch parameters |
| `AIRSPACE_TOOL_ERROR` | 503 | NOTAM service unreachable | Retry; check FAA status page |
| `TELEMETRY_UNAVAILABLE` | 403 | Flight not in "In Flight" state; WebSocket rejected | Verify flight state; connect only during active flight |

### Server Errors

| Code | Status | Message | Recovery |
|------|--------|---------|----------|
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error | Retry; contact admin if persistent |
| `DATABASE_ERROR` | 500 | Database connection failed | Retry; check database status |

---

## Implementation (FastAPI)

### Custom Exception Classes

```python
# backend/exceptions.py

class STRATOSException(Exception):
    def __init__(self, code: str, message: str, status_code: int, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class AuthException(STRATOSException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__("AUTH_INVALID", message, 401)

class PermissionException(STRATOSException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__("PERMISSION_DENIED", message, 403)

class ValidationException(STRATOSException):
    def __init__(self, field: str, message: str):
        super().__init__(
            "VALIDATION_ERROR",
            f"Invalid {field}: {message}",
            400,
            {"field": field}
        )

class NotFound(STRATOSException):
    def __init__(self, resource: str, resource_id: str):
        code = f"{resource.upper()}_NOT_FOUND"
        super().__init__(code, f"{resource} not found: {resource_id}", 404)

class StateConflict(STRATOSException):
    def __init__(self, message: str):
        super().__init__("STATE_INVALID_TRANSITION", message, 409)
```

### Exception Handler Middleware

```python
# backend/main.py

@app.exception_handler(STRATOSException)
async def stratos_exception_handler(request, exc: STRATOSException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "status": exc.status_code,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "status": 500,
                "details": {"request_id": request.headers.get("X-Request-ID")}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )
```

### Usage in Endpoints

```python
@app.get("/missions/{mission_id}")
async def get_mission(mission_id: str, user = Depends(get_current_user)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise NotFound("Mission", mission_id)
    
    # Check permission
    role = check_user_role(mission_id, user.id)
    if role is None:
        raise PermissionException("You are not a team member of this mission")
    
    return {"success": True, "data": mission}

@app.post("/flights")
async def create_flight(flight: FlightCreate, user = Depends(get_current_user)):
    if not flight.launch_date_planned:
        raise ValidationException("launch_date_planned", "Required field")
    
    if flight.launch_date_planned < datetime.now():
        raise ValidationException("launch_date_planned", "Must be in future")
    
    # Create flight
    ...
```

---

## Frontend Error Handling

### HTTP Error Interceptor

```typescript
// lib/api/client.ts

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorData = error.response?.data?.error;
    
    if (error.response?.status === 401) {
      // Auth expired; clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/';
    }
    
    if (error.response?.status === 403) {
      // Permission denied; show user-friendly message
      throw new Error(`Permission denied: ${errorData.message}`);
    }
    
    if (error.response?.status >= 500) {
      // Server error; show retry message
      throw new Error("Server error. Please try again later.");
    }
    
    // Validation or other 4xx error
    throw new Error(errorData.message || "Request failed");
  }
);
```

### React Component Error Boundary

```typescript
// components/ErrorBoundary.tsx

export class ErrorBoundary extends React.Component {
  state = { error: null, hasError: false };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-box">
          <p>Something went wrong</p>
          <p className="error-message">{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>Reload</button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### User-Facing Error Messages

```typescript
// hooks/useChat.ts

export const useChat = (missionId: string) => {
  const [error, setError] = useState<string | null>(null);
  
  const sendMessage = async (message: string) => {
    try {
      const response = await apiClient.post(
        `/missions/${missionId}/chat`,
        { message }
      );
      return response.data;
    } catch (err) {
      const message = err.message || "Failed to send message";
      setError(message);
      
      // Auto-clear after 5 seconds
      setTimeout(() => setError(null), 5000);
      
      throw err;
    }
  };
  
  return { sendMessage, error };
};
```

---

## Logging

### Backend Logging

```python
# backend/logging.py

import logging

logger = logging.getLogger(__name__)

# Log errors with context
logger.error(
    "Flight state transition failed",
    extra={
        "flight_id": flight_id,
        "current_state": flight.state,
        "requested_state": new_state,
        "user_id": user.id
    }
)

# Log warnings for external tool failures
logger.warning(
    "Weather tool unavailable; using cached data",
    extra={"flight_id": flight_id, "retry_count": 3}
)
```

### Frontend Logging

Send errors to backend logging service (Laminar/Axiom):

```typescript
// lib/logger.ts

export const logError = (code: string, message: string, context: any = {}) => {
  // Also log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error(`[${code}] ${message}`, context);
  }
  
  // Send to backend monitoring service
  fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/logs`, {
    method: 'POST',
    body: JSON.stringify({ code, message, context, timestamp: new Date() })
  });
};
```

---

## Best Practices

1. **Fail fast**: Validate input at API boundary, not deep in business logic
2. **Meaningful messages**: "Invalid launch_date_planned: Must be in future" not "Invalid field"
3. **Actionable recovery**: Tell users how to fix the problem
4. **Log context**: Include IDs, user, state before throwing
5. **Don't expose internals**: Never return stack traces to frontend; log internally only
6. **Consistent codes**: Use standard error codes so frontend can handle programmatically

---

## Next: Implement exception handlers in FastAPI

- Add exception middleware to `main.py`
- Update all endpoints to use custom exceptions
- Add logging to error handler
