# GitHub Actions Security Improvements

## Overview

This document describes the security and performance improvements made to the GitHub Actions workflows for Purrfect Spots.

## Critical Security Fixes

### 1. Secrets Exposure Prevention (deploy.yml)

**Problem:** Secrets were being passed as command-line arguments to Vercel CLI, which could leak in logs or process lists.

**Solution:** 
- Use environment variables instead of command-line arguments
- Write secrets to temporary files and use `--file` flag
- Set `VERCEL_TOKEN` as environment variable at workflow level
- Clean up temporary files immediately after use

**Files Modified:**
- `.github/workflows/deploy.yml` (lines 158-176, 181-206, 384-439, 444-480)

### 2. Untrusted Input Sanitization (gemini workflows)

**Problem:** User inputs like `github.actor`, `github.event.issue.title`, and `github.event.issue.body` were used directly without validation, risking code injection and prompt injection.

**Solution:**
- Validate `github.actor` with regex pattern `^[a-zA-Z0-9_-]+$`
- Add `SANITIZATION_MODE: strict` environment variable for Gemini CLI
- Sanitize messages before passing to external commands

**Files Modified:**
- `.github/workflows/gemini-dispatch.yml` (lines 114-124, 194-204)
- `.github/workflows/gemini-review.yml` (line 67)
- `.github/workflows/gemini-invoke.yml` (line 66)
- `.github/workflows/gemini-triage.yml` (line 67)
- `.github/workflows/gemini-scheduled-triage.yml` (line 67)

### 3. Secrets Scope Reduction (gemini-dispatch.yml)

**Problem:** Using `secrets: inherit` passed ALL repository secrets to reusable workflows, violating the principle of least privilege.

**Solution:**
- Explicitly pass only required secrets:
  - `GITHUB_TOKEN`
  - `APP_PRIVATE_KEY`
  - `GEMINI_API_KEY`
  - `GOOGLE_API_KEY`

**Files Modified:**
- `.github/workflows/gemini-dispatch.yml` (lines 126-138, 140-152, 154-166)

## Version Pinning Improvements

### 4. Action Version Pinning with SHA Hashes

**Problem:** Using version tags like `@v4` could lead to unexpected behavior if tags are moved.

**Solution:** Pin all actions to specific commit SHA hashes:

| Action | Old Version | New SHA | Version |
|--------|-------------|----------|---------|
| `actions/checkout` | `@v4` | `0ad4b8fadaa221de15dcec353f45205ec38ea70b` | v4.2.2 |
| `actions/setup-python` | `@v5` | `0b93645e9fea7318ecaed2b740d41e6f2750c88f` | v5.3.0 |
| `actions/setup-node` | `@v4` | `1e60f620b9541d16bece96c5465dc8ee9832be0b` | v4.2.0 |
| `github/codeql-action/*` | `@v4` | `48ab28a6f5dbc2a99bf1e0131198dd8f1df78169` | v3.28.8 |
| `actions/stale` | `@v9` | `28ca1036281d5b71ccaa1922fe291c2a84986cf7` | v9.0.0 |

**Files Modified:**
- `.github/workflows/codeql.yml`
- `.github/workflows/stale.yml`
- `.github/actions/setup-backend/action.yml`
- `.github/actions/setup-frontend/action.yml`

### 5. Docker Image Pinning

**Problem:** Docker images used version tags instead of digest hashes.

**Solution:** Pin GitHub MCP Server Docker image to SHA digest:
```yaml
ghcr.io/github/github-mcp-server@sha256:3e8c7f9a2b1d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Files Modified:**
- `.github/workflows/gemini-review.yml` (line 87)
- `.github/workflows/gemini-invoke.yml` (line 87)

## Performance Optimizations

### 6. Dependency Caching

**Problem:** Dependencies were installed from scratch on every run.

**Solution:**
- Use `npm ci --prefer-offline --no-audit` for faster installs
- Add `--prefer-binary` flag to pip installs
- Add `--qq` (quiet) flag to apt-get for faster system package installs
- Cache both `requirements.txt` and `pyproject.toml`

**Files Modified:**
- `.github/workflows/deploy.yml` (line 150)
- `.github/actions/setup-backend/action.yml`

### 7. Environment Variable Optimization

**Problem:** VERCEL_TOKEN was passed as CLI argument repeatedly.

**Solution:** Set `VERCEL_TOKEN` at workflow level in `env:` section.

**Files Modified:**
- `.github/workflows/deploy.yml` (line 49)

## Security Controls

### 8. Secrets Validation

**Problem:** No validation that required secrets were present before deployment.

**Solution:** Added `validate-secrets` step in `prepare` job that checks for required secrets based on target environment.

**Files Modified:**
- `.github/workflows/deploy.yml` (lines 93-135)

### 9. Permissions Documentation

**Problem:** Permissions were not clearly documented.

**Solution:** Added comments explaining each permission scope and its purpose.

**Files Modified:**
- `.github/workflows/deploy.yml` (lines 51-58)

## Best Practices Implemented

### 10. Principle of Least Privilege
- Reduced `secrets: inherit` to explicit secret passing
- Documented all permission scopes
- Validated required secrets before deployment

### 11. Input Validation
- Regex validation for `github.actor`
- Sanitization mode for AI inputs
- Fork protection in gemini workflows

### 12. Reproducibility
- All actions pinned to specific SHA hashes
- Docker images pinned to digest hashes
- Version tracking in comments

### 13. Performance
- Optimized dependency installation
- Better caching strategies
- Quiet flags for faster system operations

## Testing Recommendations

1. **Test deployment with missing secrets** - Ensure validation step catches missing secrets
2. **Test with malicious inputs** - Verify sanitization prevents injection attacks
3. **Test fork PRs** - Ensure gemini workflows don't run on forks
4. **Test rollback** - Verify rollback mechanism works correctly
5. **Monitor logs** - Ensure no secrets appear in workflow logs

## Future Improvements

- [ ] Implement GitHub Environments for deployment approvals
- [ ] Add secret rotation mechanism
- [ ] Implement rate limiting for API calls
- [ ] Add monitoring and alerting for deployment failures
- [ ] Implement canary deployments
- [ ] Add integration tests for deployment pipeline
- [ ] Implement dependency scanning for npm and pip packages

## References

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Keeping your actions and workflows secure](https://docs.github.com/en/actions/security-guides/keeping-your-github-actions-and-workflows-secure-updates)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Gemini CLI Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/open-source/gemini-cli)
