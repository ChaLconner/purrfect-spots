# Purrfect Spots Coding Standards

## 1. Core Principles
- **Strict Typing**: No `any` (unless documented/3rd-party).
- **Zero Lint Errors**: `ruff` (Backend), `eslint` (Frontend).
- **Clean Code**: Readable, self-documenting, single responsibility.
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

## 3. Backend (Python)
- **Tools**: `ruff`, `mypy`.
- **Naming**: `snake_case` (vars/funcs), `PascalCase` (classes), `UPPER_CASE` (consts), `_leading` (private).
- **Typing**: Mandatory annotations. Use `Optional[T]` or `T | None`.
- **Errors**: Raise custom exceptions in Services. Handle in Routes/Global Handler.
- **DI**: Use `Depends` for service injection.
- **Docs**: Google Style docstrings for public members.

## 4. Frontend (Vue/TS)
- **Tools**: `eslint`, `prettier`, `vue-tsc`.
- **Naming**: `PascalCase` (Files/Components), `camelCase` (vars/funcs).
- **Components**: `<script setup lang="ts">`. Logic in `computed`/composables.
- **Typing**: No explicit `any`. Interface all props/emits. Zod for API data.
- **State**: Pinia Setup Stores (`ref()`). Explicit types.
- **Styling**: Tailwind CSS utilities. Avoid `@apply` and raw CSS.

## 5. Testing
- **Backend (pytest)**: Mock external deps (DB/S3). Test Services isolated. Integration via `TestClient`.
- **Frontend**: `vitest` (logic/components), `playwright` (E2E flows).

## 6. Git & Workflow
- **Commits**: Conventional (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- **Branches**: `main` (prod), `feature/*`, `fix/*`.
- **Pre-commit**: Lint/Type-check must pass.

## 7. Config & Secrets
- **Env Vars**: `.env` only. Access via `config.py` (BE) or `import.meta.env` (FE).
- **Secrets**: NEVER commit. Use `.env.example`.

## 8. Enforcement
CI/CD runs `ruff`, `mypy`, `npm run lint/type-check`. **Zero tolerance.**
