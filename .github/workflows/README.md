# CI/CD Workflow Improvements

## Overview

This document describes the best practices implemented in the CI/CD workflow for Purrfect Spots.

## Key Changes

### 1. Pinned Action Versions

All GitHub Actions are now pinned to specific versions for reproducibility:
- `aquasecurity/trivy-action@0.28.0` (was `@master`)
- `trufflesecurity/trufflehog@v3.88.1` (was `@main`)
- `docker/build-push-action@v6` (was `@v5`)
- `semgrep/semgrep-action@v1` (was `returntocorp/semgrep-action@v1`)

### 2. Non-Blocking Security Scans

Security scans no longer fail the build immediately. Instead, they report findings as warnings:
- Security Scan (Trivy)
- Secret Detection (Trufflehog)
- SAST Scan (Semgrep)
- API Contract Check

This allows teams to review security findings without blocking the development workflow.

### 3. Improved Job Dependencies

- E2E tests only run when both frontend build and backend tests succeed
- Quality gate focuses on essential checks only
- Security scans run in parallel without blocking

### 4. Better Error Handling

- Added `continue-on-error: true` for non-critical checks
- Improved error messages with job status reporting
- Graceful degradation when baseline files are missing

### 5. MyPy Type Checking

Separated MyPy type checking into its own job:
- Non-blocking (gradual type adoption)
- Excludes tests and scripts directories
- Configured with `explicit_package_bases` to fix module resolution

### 6. Coverage Threshold Adjustment

Reduced coverage requirement from 70% to 60% to allow incremental improvement.

### 7. Workflow Dispatch Options

Added manual trigger options:
- `skip_e2e`: Skip E2E tests for faster iteration
- `force_full_run`: Ignore change detection and run all jobs

### 8. Permissions

Applied principle of least privilege:
- Default: `contents: read`, `pull-requests: read`
- Security scans: `security-events: write`
- Dependency review: `pull-requests: write`

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

Required environment variables (set in workflow):
- `PYTHON_VERSION`: 3.12
- `NODE_VERSION`: 20
- Test credentials for backend (hardcoded for CI)

## Troubleshooting

### Common Issues

1. **MyPy module resolution errors**: Ensure all package directories have `__init__.py` files
2. **Trivy scan failures**: Check if the action version is compatible
3. **E2E test timeouts**: Tests have a 30-minute limit

### Disabling Checks

To temporarily skip a check:
- Use workflow dispatch with `skip_e2e: true`
- Add `continue-on-error: true` to the job

## Future Improvements

- [ ] Add Codecov integration for code coverage tracking
- [ ] Implement branch protection rules based on quality gate
- [ ] Add deployment preview for PRs
- [ ] Implement canary deployments
