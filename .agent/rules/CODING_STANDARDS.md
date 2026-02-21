# Purrfect Spots Coding Standards

> **Note:** For concrete code examples and patterns related to these standards, please refer to [BEST_PRACTICES.md](./BEST_PRACTICES.md).

## 1. Core Principles
- **Strict Typing**: No `any` (unless documented/3rd-party).
- **Zero Lint Errors**: `ruff` (Backend), `eslint` (Frontend).
- **Clean Code**: Readable, self-documenting, single responsibility.
- **Componentization & File Size**: Keep files small and focused. Aim for a maximum of 250-300 lines per file. Break down large files into smaller, reusable components or modules.
- **Security**: No secrets in repo. Validate all inputs (Zod/Pydantic). Generic prod errors.

## 2. Architecture (Monorepo)
### Backend (FastAPI, Python 3.12+)
- **Routes**: Controller layer. Min business logic. Calls Services.
- **Services**: Pure business logic. No HTTP deps.
- **Schemas**: Pydantic DTOs.
- **Utils**: Stateless helpers.

### Frontend (Vue 3, TS, Pinia)
- **Views**: Page components.
- **Components**: Reusable UI.
- **Stores**: Pinia Setup Stores.
- **Composables**: Stateful logic.

## 3. API Design & Responses
- **Standard Format**: Use structured JSON responses for consistency (e.g., JSend format).
- **Error Handling**: Raise Custom Exceptions in Services. Map them to correct HTTP Status Codes via Global Error Handler. Return specific payload: `{"error_code": "...", "message": "...", "details": {}}`.

## 4. Backend (Python)
- **Tools**: `ruff`, `mypy`.
- **Naming**: `snake_case` (vars/funcs), `PascalCase` (classes), `UPPER_CASE` (consts), `_leading` (private).
- **Typing**: Mandatory annotations. Use `Optional[T]` or `T | None`.
- **DI**: Use `Depends` for service injection.
- **Docs**: Google Style docstrings for public members.
- **Async Rules**: Do not block the event loop. Run CPU-bound or blocking I/O tasks (like standard synchronous HTTP calls) via Thread Pool or async equivalents.

## 5. Database & ORM
- **Logic**: No business logic in DB schema (e.g., avoid Triggers). Handle in code.
- **Performance**: Avoid N+1 Query problems. Enforce eager loading (e.g., `joinedload`, `selectinload` in SQLAlchemy) for relations.
- **Transactions**: Manage transactions carefully, maintaining atomicity at the Service layer.

## 6. Frontend (Vue/TS)
- **Tools**: `eslint`, `prettier`, `vue-tsc`.
- **Naming**: `PascalCase` (Files/Components), `camelCase` (vars/funcs).
- **Components**: `<script setup lang="ts">`. Logic in `computed`/composables.
- **Typing**: No explicit `any`. Interface all props/emits. Zod for API data.
- **State**: Pinia Setup Stores (`ref()`). Explicit types.
- **Styling**: Tailwind CSS utilities. Avoid `@apply` and raw CSS.
- **Async/API Rules**: Wrap Axios/Fetch calls in `try/catch`. Always manage Loading/Error states properly to prevent UI freezes.

## 7. Logging, Monitoring & Sentry
- **Logging**: No `print()`. Use a structured logger.
- **Sentry**: Catch expected errors to reduce noise. Add context (User ID, Trace ID, Request ID) to Sentry events. Scrub PII (Personally Identifiable Information) and sensitive data from logs.

## 8. Testing
- **Backend (pytest)**: Mock external deps (DB/S3). Test Services isolated. Integration via `TestClient`.
- **Frontend**: `vitest` (logic/components), `playwright` (E2E flows).

## 9. Git, Workflow & Code Review
- **Commits**: Conventional (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- **Branches**: `main` (prod), `feature/*`, `fix/*`.
- **Pre-commit**: Lint/Type-check must pass.
- **Pull Requests**: Required for `main`. No direct pushes. Must be linked to an Issue.
- **Code Review**: PRs must pass CI (100%) and require at least **1 Reviewer Approval**. Reviewers must check for architectural compliance and edge cases, not just syntax.

## 10. Config & Secrets
- **Env Vars**: `.env` only. Access via `config.py` (BE) or `import.meta.env` (FE).
- **Secrets**: NEVER commit. Use `.env.example`.

## 11. Enforcement
CI/CD runs `ruff`, `mypy`, `npm run lint/type-check`. **Zero tolerance.**
