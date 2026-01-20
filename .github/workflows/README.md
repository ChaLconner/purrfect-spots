# GitHub Workflows

This directory contains all CI/CD workflows for the Purrfect Spots project.

## 📋 Workflow Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main, develop | Main CI/CD pipeline |
| `codeql.yml` | Push/PR to main, Schedule | Security analysis |
| `pr-labeler.yml` | Pull requests | Auto-labeling |
| `stale.yml` | Daily schedule | Stale issue management |

## 🔧 Main CI Pipeline (`ci.yml`)

The main CI/CD pipeline includes:

### Backend Jobs
- **Backend Lint** - Ruff linting and formatting check
- **Backend Test** - Pytest with coverage (70% threshold)
- **API Contract Check** - OpenAPI breaking change detection
- **Backend Docker Build** - Docker image build verification

### Frontend Jobs
- **Frontend Lint** - ESLint and TypeScript check
- **Frontend Test** - Vitest unit tests with coverage
- **Frontend Build** - Production bundle build
- **Frontend Docker Build** - Docker image build verification

### Security Jobs
- **Security Scan** - Trivy vulnerability scanning
- **Secret Scan** - Trufflehog secret detection
- **SAST Scan** - Semgrep static analysis
- **Dependency Review** - License and vulnerability check (PRs only)

### E2E Testing
- **E2E Tests** - Playwright browser tests (Chromium)

### Quality Gates
- All jobs must pass before merge is allowed

## 🏷️ PR Labels

PRs are automatically labeled based on:

- **Files changed** - `backend`, `frontend`, `ci`, etc.
- **PR size** - `size/XS`, `size/S`, `size/M`, `size/L`, `size/XL`

See `.github/labeler.yml` for full configuration.

## 🛡️ Security Scanning

### CodeQL
Runs deep semantic analysis for:
- JavaScript/TypeScript vulnerabilities
- Python vulnerabilities

### Trivy
Scans for:
- Dependency vulnerabilities
- Misconfiguration issues

### Semgrep
Checks for:
- OWASP Top 10 issues
- Security audit patterns

### TruffleHog
Detects:
- Accidentally committed secrets
- API keys in history

## ⏰ Stale Issues

Issues and PRs are automatically marked stale:

| Type | Stale After | Close After |
|------|-------------|-------------|
| Issues | 30 days | 14 days |
| PRs | 14 days | 7 days |

To prevent auto-closing:
- Add `keep-open` label to issues
- Add `work-in-progress` label to PRs

## 🔄 Dependabot

Dependabot is configured to:
- Update Python dependencies weekly
- Update npm dependencies weekly
- Update GitHub Actions weekly
- Update Docker images weekly

See `.github/dependabot.yml` for full configuration.

## 🚀 Running Locally

To run the CI checks locally:

### Backend
```bash
cd backend
pip install ruff pytest pytest-cov
ruff check .
ruff format --check .
pytest --cov=. --cov-fail-under=70
```

### Frontend
```bash
cd frontend
npm ci
npm run type-check
npm run lint:check
npm run test
npm run build
```

### E2E Tests
```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

## 🐛 Troubleshooting

### E2E Tests Timeout
If E2E tests timeout:
1. Check if the backend health check passes
2. Check Playwright report artifact for details
3. Increase `timeout-minutes` in the workflow if needed

### Coverage Threshold Not Met
If coverage fails:
1. Backend requires 70% coverage minimum
2. Write more tests for uncovered code
3. Check coverage report artifacts for details
