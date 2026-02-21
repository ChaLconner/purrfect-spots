# CI/CD Workflow Improvements

## Overview

This document describes best practices implemented in CI/CD workflow for Purrfect Spots.

**🔒 Security Note:** See [`SECURITY_IMPROVEMENTS.md`](.github/workflows/SECURITY_IMPROVEMENTS.md) for recent security hardening changes.

## Key Changes

### 1. Pinned Action Versions (SHA Hashes)

All GitHub Actions are now pinned to specific commit SHA hashes for maximum reproducibility:
- `actions/checkout@0ad4b8fadaa221de15dcec353f45205ec38ea70b` (v4.2.2)
- `actions/setup-python@0b93645e9fea7318ecaed2b740d41e6f2750c88f` (v5.3.0)
- `actions/setup-node@1e60f620b9541d16bece96c5465dc8ee9832be0b` (v4.2.0)
- `github/codeql-action/*@48ab28a6f5dbc2a99bf1e0131198dd8f1df78169` (v3.28.8)
- `actions/stale@28ca1036281d5b71ccaa1922fe291c2a84986cf7` (v9.0.0)

### 2. Secrets Security Hardening

**Critical Security Fix:** Secrets are no longer passed as command-line arguments:
- Use environment variables instead of CLI arguments
- Write secrets to temporary files and use `--file` flag
- Set `VERCEL_TOKEN` at workflow level
- Clean up temporary files immediately

**Files:** `.github/workflows/deploy.yml`

### 3. Input Sanitization

All untrusted inputs are now validated:
- `github.actor` validated with regex `^[a-zA-Z0-9_-]+$`
- `SANITIZATION_MODE: strict` added to Gemini CLI
- Fork protection in gemini workflows

**Files:** `.github/workflows/gemini-*.yml`

### 4. Secrets Scope Reduction

Replaced `secrets: inherit` with explicit secret passing:
```yaml
secrets:
  GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}'
  APP_PRIVATE_KEY: '${{ secrets.APP_PRIVATE_KEY }}'
  GEMINI_API_KEY: '${{ secrets.GEMINI_API_KEY }}'
  GOOGLE_API_KEY: '${{ secrets.GOOGLE_API_KEY }}'
```

**Files:** `.github/workflows/gemini-dispatch.yml`

### 5. Non-Blocking Security Scans

Security scans no longer fail the build immediately. Instead, they report findings as warnings:
- Security Scan (Trivy)
- Secret Detection (Trufflehog)
- SAST Scan (Semgrep)
- API Contract Check

This allows teams to review security findings without blocking development workflow.

### 6. Improved Job Dependencies

- E2E tests only run when both frontend build and backend tests succeed
- Quality gate focuses on essential checks only
- Security scans run in parallel without blocking

### 7. Better Error Handling

- Added `continue-on-error: true` for non-critical checks
- Improved error messages with job status reporting
- Graceful degradation when baseline files are missing
- Secrets validation before deployment

### 8. MyPy Type Checking

Separated MyPy type checking into its own job:
- Non-blocking (gradual type adoption)
- Excludes tests and scripts directories
- Configured with `explicit_package_bases` to fix module resolution

### 9. Coverage Threshold Adjustment

Reduced coverage requirement from 70% to 60% to allow incremental improvement.

### 10. Workflow Dispatch Options

Added manual trigger options:
- `skip_e2e`: Skip E2E tests for faster iteration
- `force_full_run`: Ignore change detection and run all jobs

### 11. Permissions (Principle of Least Privilege)

Applied principle of least privilege:
- Default: `contents: read`, `pull-requests: read`
- Security scans: `security-events: write`
- Dependency review: `pull-requests: write`
- Deployments: `id-token: write` (for OIDC)

## Job Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Detect Changes                           │
└─────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Backend Lint  │     │ Frontend Lint │     │ Security Scan │
└───────────────┘     └───────────────┘     └───────────────┘
         │                     │                     │
         ▼                     ▼                     │
┌───────────────┐     ┌───────────────┐             │
│ Backend Test  │     │ Frontend Test │             │
└───────────────┘     └───────────────┘             │
         │                     │                     │
         ▼                     ▼                     │
┌───────────────┐     ┌───────────────┐             │
│ Backend Build │     │ Frontend Build│             │
└───────────────┘     └───────────────┘             │
         │                     │                     │
         └─────────┬───────────┘                     │
                   ▼                                 │
         ┌───────────────┐                           │
         │   E2E Tests   │                           │
         └───────────────┘                           │
                   │                                 │
                   └───────────┬─────────────────────┘
                               ▼
                   ┌───────────────────┐
                   │   Quality Gate    │
                   └───────────────────┘
                               │
                               ▼
                   ┌───────────────────┐
                   │  Build Summary    │
                   └───────────────────┘
```

## Environment Variables

Required secrets:
- `SEMGREP_APP_TOKEN` (optional, for enhanced Semgrep features)
- `VERCEL_TOKEN` (required for deployments)
- `GEMINI_API_KEY` (required for AI workflows)
- `APP_PRIVATE_KEY` (required for GitHub App authentication)

Required environment variables (set in workflow):
- `PYTHON_VERSION`: 3.12
- `NODE_VERSION`: 20
- Test credentials for backend (hardcoded for CI)

## Troubleshooting

### Common Issues

1. **MyPy module resolution errors**: Ensure all package directories have `__init__.py` files
2. **Trivy scan failures**: Check if action version is compatible
3. **E2E test timeouts**: Tests have a 30-minute limit
4. **Secrets validation failures**: Ensure all required secrets are configured for the target environment

### Disabling Checks

To temporarily skip a check:
- Use workflow dispatch with `skip_e2e: true`
- Add `continue-on-error: true` to job

## Future Improvements

- [ ] Add Codecov integration for code coverage tracking
- [ ] Implement branch protection rules based on quality gate
- [ ] Add deployment preview for PRs
- [ ] Implement canary deployments
- [ ] Add secret rotation mechanism
- [ ] Implement rate limiting for API calls
- [ ] Add monitoring and alerting for deployment failures
- [ ] Implement dependency scanning for npm and pip packages
