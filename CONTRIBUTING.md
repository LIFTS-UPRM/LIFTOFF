# Contributing to STRATOS

Thank you for contributing to STRATOS. This document covers the branch strategy, pull request workflow, and CI checks that every contributor should follow.

---

## Branch Strategy

| Branch | Purpose | Push policy |
|--------|---------|-------------|
| `main` | Stable, deployable code | Protected — PRs only |
| `feature/<name>` | New features | Push freely, open PR when ready |
| `fix/<name>` | Bug fixes | Push freely, open PR when ready |
| `chore/<name>` | Tooling, docs, cleanup | Push freely, open PR when ready |

**No one pushes directly to `main`.** All changes arrive through a pull request.

---

## Opening a Pull Request

1. **Branch off `main`** before starting work.

   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes.** Keep commits focused and descriptive.

3. **Push your branch** to GitHub.

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a pull request** against `main` on GitHub.
   - Write a clear title and a short description of what changed and why.
   - Reference any related issue (e.g. `Closes #42`).

5. **Wait for CI to pass.** Both the frontend and backend checks must be green before the PR can be merged.

6. **Request a review.** At least one team member must approve before merging.

7. **Address review feedback**, then merge once approved and CI is green.

---

## CI Checks

CI runs automatically on every pull request targeting `main` and on every push to non-main branches. Three workflows run in parallel:

### Frontend CI (`frontend-ci.yml`)

| Step | Command | Fails if... |
|------|---------|-------------|
| Install deps | `npm ci` | `package-lock.json` is out of sync |
| Lint | `npm run lint` | ESLint errors exist |
| Build | `npm run build` | TypeScript or Next.js build errors |

### Backend CI (`backend-ci.yml`)

| Step | Command | Fails if... |
|------|---------|-------------|
| Install deps | `pip install -r requirements.txt -r requirements-dev.txt` | A package fails to install |
| Lint | `ruff check .` | Ruff style violations exist |
| Import validation | `python -c "import main"` | The app cannot be imported (broken imports, syntax errors) |
| Tests | `pytest` | Any test fails (runs only if a `tests/` directory exists) |

### Security CI (`security-ci.yml`)

| Step | Command | Fails if... |
|------|---------|-------------|
| Backend security scan | `bandit -r app mcp_servers main.py llm.py -x tests,vendor --skip B104 --severity-level medium --confidence-level medium` | Bandit finds a medium-or-higher confidence security issue in STRATOS backend code |
| Frontend dependency audit | `npm audit --audit-level=high` | npm reports a high-or-critical advisory for installed frontend dependencies |

Security checks intentionally scan STRATOS-owned backend code and exclude `backend/vendor/` so vendored HAB predictor code does not drown out actionable findings. Bandit `B104` is skipped because the API bind host is deployment-configurable and currently defaults to `0.0.0.0`. Add new suppressions only when a finding is reviewed and intentional.

A PR **cannot be merged** if any CI job is failing.

---

## Branch Protection Rules (enforced on `main`)

- Pull request required before merging
- At least 1 approving review required
- Stale approvals dismissed when new commits are pushed
- All conversations must be resolved before merge
- Status checks (`Frontend CI`, `Backend CI`, and `Security CI`) must pass before merge
- Direct pushes to `main` are blocked

---

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev       # Dev server at http://localhost:3000
npm run lint      # Run ESLint
npm run build     # Production build check
```

### Backend

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn main:app --reload   # Dev server at http://localhost:8000
ruff check .                # Lint
pytest                      # Run tests (when tests exist)
bandit -r app mcp_servers main.py llm.py -x tests,vendor --skip B104 --severity-level medium --confidence-level medium
```

Copy `.env.example` to `.env` and fill in your local values before running the backend.

### Security checks

Run the same security checks as CI before opening a PR:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
bandit -r app mcp_servers main.py llm.py -x tests,vendor --skip B104 --severity-level medium --confidence-level medium
```

```bash
cd frontend
npm ci
npm audit --audit-level=high
```

---

## Definition of Done

A PR is ready to merge when:

- [ ] CI is green (both frontend and backend checks pass)
- [ ] At least 1 team member has approved
- [ ] All review comments are resolved
- [ ] The branch is up to date with `main`
