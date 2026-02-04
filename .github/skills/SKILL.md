---
name: Staff-Level Enterprise Quality & Security Verification
description: The ultimate verification protocol for enterprise-grade, zero-defect, and compliant software engineering.
---

# 🏆 Staff-Level Enterprise Quality & Security Verification Skill

As a Staff Engineer, you are the guardian of the system's architecture, stability, and legal safety. **MANDATORY EXECUTION OF ALL STEPS.** No shortcuts, no compromises. Every commit must be a benchmark of excellence.

## 🏛️ 1. Architectural Integrity & Deep Performance

- [ ] **Comprehensive Logic Audit (Line-by-Line):**
  - Read every changed line. Do not just look at diffs.
  - **Edge Cases:** What happens if the input is `None`, an empty string, or a extremely large payload?
  - **Race Conditions:** If two requests happen simultaneously, does the state remain consistent?
- [ ] **Idempotency & Reliability (Retry Safety):**
  - Ensure `POST`, `PUT`, and `PATCH` operations can be retried without side effects.
  - **Verification:** Check if there is a unique request ID or a database constraint preventing duplicate entries for the same action.
- [ ] **Data Performance (SQL Deep Dive):**
  - **EXPLAIN ANALYZE:** For any new or modified query, run `EXPLAIN ANALYZE` in the DB.
  - **Checklist:** Are we hitting an Index? Is there any "Sequential Scan"? Is the "Cost" acceptable for high-traffic tables?
- [ ] **N+1 Query Prevention:**
  - Audit `joinedload` or `selectinload` for every relationship access in loops.
  - **Verification:** Monitor DB logs during a test run to ensure only expected queries are executed.
- [ ] **Resource Optimization & Resilience:**
  - Check for memory leaks (e.g., large lists held in memory).
  - Ensure CPU-intensive tasks are offloaded to background workers (Celery/APScheduler) if they take >500ms.
  - **Resilience:** Ensure all external API calls have explicit **Timeouts**. Implement **Circuit Breakers** for non-critical dependencies to prevent cascading failures.

## 🐍 2. Backend & API Excellence (Python/FastAPI)

- [ ] **API Contract & Backward Compatibility:**
  - **Breaking Changes:** Did you rename a field, change a type, or remove an endpoint? If yes, is the version (e.g., `/v1/` to `/v2/`) updated?
  - **OpenAPI Clarity & Contract:** Run the app and check `/docs`. Is it accurate? Use Pydantic's `Field(..., example=..., description=...)` to make the contract self-explanatory.

- [ ] **Strict Typing (Zero 'Any' Tolerance):**
  - Run `mypy .`. Every function must have type hints for arguments and return types.
  - Use `Final`, `Literal`, and `TypedDict` for complex structures to ensure full type safety.
- [ ] **Database Migrations (Alembic):**
  - **Verify Both Ways:** Run `alembic upgrade head` then `alembic downgrade -1`.
  - **Data Integrity:** Does the migration handle existing data? (e.g., adding a NOT NULL column requires a default or a data-fill script).
- [ ] **Test Rigor & Coverage:**
  - Run `pytest --cov=backend --cov-report=term-missing`.
  - **Requirement:** 100% coverage on the lines *you* changed. No excuses.
- [ ] **Observability & Logging:**
  - Use `logger.error("Context info", extra={"data": user_id})` instead of raw print.
  - Ensure Sentry integration is triggered for critical failures with appropriate tags.

## ⚛️ 3. Frontend Excellence (Vue/TS/Vite)

- [ ] **Type Integrity (vue-tsc):**
  - Run `npm run type-check`. No `ts-ignore` allowed without a senior-level justification comment.
  - Ensure Props and Emits are strictly typed.
- [ ] **Responsive & UX Polish:**
  - **Breakpoints:** Test on 375px (Mobile), 768px (Tablet), and 1440px+ (Desktop).
  - **States:** Do all buttons have `:hover`, `:active`, and `:disabled` states? Is there a loading spinner for async actions?
- [ ] **Refactoring & Code Smells:**
  - Are components too large (>300 lines)? Split them.
  - Is logic duplicated across components? Move to a Composable (`useSharedLogic.ts`).
- [ ] **Automated Tests:**
  - **Unit:** `npm run test` (Vitest).
  - **E2E:** `npm run test:e2e` (Playwright). If you touched the Auth or Checkout flow, this is MANDATORY.

## 🔒 4. Security, License & Compliance

- [ ] **Security Hotspots Manual Review:**
  - **Authentication:** Are you checking JWT validity correctly?
  - **Authorization:** Can user A access user B's data by changing an ID (IDOR check)?
  - **Inputs:** Are you sanitzing user inputs to prevent XSS or SQL Injection?
  - **Availability:** Have you applied **Rate Limiting** to public or sensitive endpoints (Login, SMS/Email OTP, Search) to prevent DoS/Brute-force?
- [ ] **Secret Management (Zero Leakage):**
  - Run `detect-secrets scan`. Never commit `.env` or hardcoded keys.
  - If a secret was accidentally added, rotate it immediately and purge history.
- [ ] **Dependency & License Audit:**
  - Run `trivy fs . --scanners vuln`.
  - **Licenses:** Check `package.json` for new libraries. Avoid GPL/AGPL unless approved. Use MIT/Apache/BSD.
- [ ] **Environment Sync:**
  - If you added a key to `.env`, you MUST add it to `.env.example` with a dummy value.

## 🧹 5. Repository Hygiene & Documentation

- [ ] **Git Status Cleanup:**
  - Run `git status`. Remove `.DS_Store`, `__pycache__`, or temp logs.
  - Ensure only relevant files are staged.
- [ ] **Staff-Level Documentation:**
  - Update `README.md` if the setup changed.
  - Add Docstrings (`""" ... """`) to all new classes and public methods.
- [ ] **Professional Commit Messages:**
  - Format: `<type>(<scope>): <subject>`
  - Example: `feat(auth): implement 2FA using TOTP` or `fix(db): resolve deadlock in transaction update`
  - Description: Briefly explain the "Why" and any architectural decisions made.

---

## 🛠️ Step-by-Step Verification Protocol (Copy-Paste)

Execute these commands in order. **If any command fails, fix it before moving to the next.**

```bash
# 1. Backend Rigor
cd backend
ruff check . --fix && ruff format .
mypy .
pytest --cov=backend --cov-report=term-missing

# 2. Frontend Rigor
cd ../frontend
npm run lint
npm run type-check
npm run test

# 3. Security & Compliance
cd ..
trivy fs . --scanners vuln,secret,config
# Double check .env.example
```

> [!DANGER]
> **A STAFF ENGINEER NEVER COMMITS "GOOD ENOUGH".** We commit perfection. If you are tired, take a break. Do not lower the standard.
