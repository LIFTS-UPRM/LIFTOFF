# Deployment Runbook

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: DevOps, Release managers

---

## Overview

STRATOS deployment pipeline: code → GitHub → CI/CD → staging → production.

**Environments**:
- **Development**: Localhost (npm run dev, uvicorn)
- **Staging**: Internal test environment (optional, before prod)
- **Production**: Live deployment for LIFTS

---

## CI/CD Pipeline (GitHub Actions)

### Frontend CI

Trigger: Push to branch or PR to main

```yaml
# .github/workflows/frontend.yml

name: Frontend CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 20
      - run: npm ci --prefix frontend
      - run: npm run lint --prefix frontend
      - run: npm run build --prefix frontend
      - run: npm audit --audit-level=high --prefix frontend
```

### Backend CI

```yaml
# .github/workflows/backend.yml

name: Backend CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
      - run: cd backend && ruff check .
      - run: cd backend && python -c "import main"
      - run: cd backend && pytest
      - run: cd backend && bandit -r app mcp_servers main.py llm.py -x tests,vendor --severity-level medium
```

---

## Pre-Deployment Checklist

- [ ] All tests passing (CI/CD green)
- [ ] Code reviewed and approved
- [ ] Secrets (API keys, database credentials) added to deployment environment
- [ ] Database migrations ready (if schema changes)
- [ ] Release notes prepared
- [ ] Rollback plan documented

---

## Deployment Steps

### 1. Prepare Release

```bash
# Create release branch
git checkout -b release/v1.0.0

# Update version in package.json, pyproject.toml, etc.
# Commit changes
git commit -am "chore: bump version to 1.0.0"

# Tag release
git tag v1.0.0
git push origin release/v1.0.0 --tags
```

### 2. Deploy Backend

**Option A: Manual (for small deployments)**

```bash
# SSH into production server
ssh stratos-api.lifts.uprm.edu

# Pull latest code
cd /app/stratos-backend
git fetch origin
git checkout v1.0.0

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if needed)
alembic upgrade head

# Restart service
systemctl restart stratos-backend

# Verify health check
curl https://api.stratos.lifts.uprm.edu/health
```

**Option B: Docker (recommended)**

```bash
# Build image
docker build -t stratos-backend:v1.0.0 -f backend/Dockerfile .

# Push to registry
docker push registry.example.com/stratos-backend:v1.0.0

# Update deployment
kubectl set image deployment/stratos-backend stratos-backend=registry.example.com/stratos-backend:v1.0.0
kubectl rollout status deployment/stratos-backend
```

### 3. Deploy Frontend

```bash
# Build production bundle
npm ci --prefix frontend
npm run build --prefix frontend

# Deploy to hosting (e.g., Vercel, AWS S3 + CloudFront)
npm run deploy --prefix frontend

# Or: Docker + Kubernetes
docker build -t stratos-frontend:v1.0.0 -f frontend/Dockerfile .
docker push registry.example.com/stratos-frontend:v1.0.0
kubectl set image deployment/stratos-frontend stratos-frontend=registry.example.com/stratos-frontend:v1.0.0
```

### 4. Verify Deployment

```bash
# Frontend
curl https://stratos.lifts.uprm.edu

# Backend health
curl https://api.stratos.lifts.uprm.edu/health

# Test login flow
# Manual smoke test in browser

# Monitor logs
kubectl logs -f deployment/stratos-backend
kubectl logs -f deployment/stratos-frontend
```

---

## Rollback Plan

If deployment fails or bugs discovered:

```bash
# Rollback to previous image
kubectl rollout undo deployment/stratos-backend
kubectl rollout undo deployment/stratos-frontend

# Verify rollback
kubectl rollout status deployment/stratos-backend

# Or: Revert tag to previous version and redeploy
git checkout v0.9.9
# Redeploy...
```

---

## Database Migrations

If schema changes needed:

```bash
# Create migration
alembic revision --autogenerate -m "Add Flight state field"

# Review migration file
cat backend/migrations/versions/xxx_add_flight_state.py

# Test locally
alembic upgrade head

# On production: run before restarting service
alembic upgrade head

# To rollback (if needed)
alembic downgrade -1
```

---

## Environment Variables

**Backend (.env)**:
```
LLM_API_KEY=sk_...
LLM_MODEL=gpt-4o-mini
FAA_CLIENT_ID=...
FAA_CLIENT_SECRET=...
DATABASE_URL=postgresql://user:pass@db.example.com/stratos
SUPABASE_URL=https://xyzabc.supabase.co
SUPABASE_KEY=...
LAMINAR_USER_KEY=...
```

**Frontend (.env.local)**:
```
NEXT_PUBLIC_BACKEND_URL=https://api.stratos.lifts.uprm.edu
NEXT_PUBLIC_SUPABASE_URL=https://xyzabc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

**Store in**: GitHub Actions secrets, Kubernetes secrets, or secret management service.

---

## Monitoring & Alerts

### Health Checks

Backend: `GET /health` → 200 OK, uptime

```python
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "uptime": time.time() - start_time,
        "timestamp": datetime.utcnow()
    }
```

### Logging

- **Backend**: Laminar/Axiom (structured logging)
- **Frontend**: Client error tracking (Sentry or custom)
- **Infrastructure**: Server metrics (CPU, memory, disk)

### Alerts

- High error rate (>1% of requests)
- Database connection failures
- WebSocket broadcast failures
- External tool failures (weather, trajectory)

---

## Scaling Considerations

### Horizontal Scaling (Multiple Instances)

```yaml
# Kubernetes deployment (optional future)
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stratos-backend
  template:
    spec:
      containers:
      - name: stratos-backend
        image: stratos-backend:v1.0.0
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Load Balancing

- Frontend: CDN (Cloudflare, AWS CloudFront)
- Backend: Load balancer (AWS ALB, nginx)
- WebSocket: Sticky sessions (affinity to same backend instance)

### Database

- Read replicas for scaling (async backup)
- Connection pooling (PgBouncer)
- Caching layer (Redis) for high-traffic queries

---

## Disaster Recovery

### Backup Strategy

- **Database**: Daily snapshots to S3
- **Code**: GitHub as source of truth
- **Secrets**: Encrypted backup of .env files

### Recovery Time Objective (RTO)

- **API**: < 5 minutes (restore from backup, redeploy)
- **Database**: < 1 hour (restore from snapshot)

### Recovery Point Objective (RPO)

- **Database**: 1 day (daily snapshots)
- **Code**: < 1 minute (git commits)

---

## Maintenance Windows

Schedule maintenance during low-traffic hours (e.g., weekends, late evenings).

### Example: Database Upgrade

1. Announce maintenance window to team
2. Take database snapshot
3. Upgrade database version (or move to new instance)
4. Run migrations
5. Test connectivity from backend
6. Monitor for 30 minutes
7. Close maintenance window

---

## Support Contacts

- **Backend Issues**: @armando (DevOps)
- **Frontend Issues**: @frontend-lead
- **Infrastructure**: @infrastructure-team
- **On-call**: Rotating duty (schedule in GitHub)

---

## Next: Prepare Dockerfile and Kubernetes configs

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `k8s/deployment.yaml` (optional)
