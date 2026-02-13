# Purrfect Spots Coding Standards & Guidelines

This document outlines the coding standards, style guides, and best practices for the Purrfect Spots project. All contributors must adhere to these rules to ensure code quality, maintainability, and consistency.

## General Principles

1. **Strict Typing**: All code (Frontend & Backend) must be strictly typed. `any` is forbidden unless absolutely necessary and documented with a comment explaining why.
2. **Linting**: No linting errors should be committed. Use the provided tools (`ruff`, `eslint`) to check your code.
3. **Clean Code**: Write readable, self-documenting code. Use meaningful variable and function names.
4. **No Magic Numbers/Strings**: Use constants or configuration files for literal values.
5. **Error Handling**: Handle errors gracefully. Don't suppress exceptions without logging or handling them.

---

## Backend (Python)

We use **Python 3.12+**.

### Tools

- **Linter**: `ruff`
- **Type Checker**: `mypy`
- **Formatter**: `ruff format`

### Python Coding Rules

1. **Type Annotations**:
    - **All function arguments and return values must be typed.**
    - Use `Optional[T]` or `T | None` for values that can be None.
    - Use `Final` for constants.
    - Avoid `Any`. Use `object` or specific types/protocols if `Any` seems necessary.

    ```python
    # BAD
    def process_data(data):
        return data["id"]

    # GOOD
    from typing import Any, Dict

    def process_data(data: Dict[str, Any]) -> int:
        return int(data["id"])
    ```

2. **Naming Conventions**:
    - **Variables/Functions**: `snake_case` (e.g., `user_id`, `get_user_profile`)
    - **Classes**: `CapWords` (PascalCase) (e.g., `UserProfile`, `AuthService`)
    - **Constants**: `UPPER_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
    - **Private Members**: `_leading_underscore` (e.g., `_internal_helper`)

3. **Imports**:
    - Group imports: Standard library, Third-party, Local application.
    - Use absolute imports for local modules (e.g., `from app.services import user_service` instead of `from ..services import user_service`).

4. **Docstrings**:
    - Public modules, classes, and functions should have docstrings (Google style or NumPy style preferred).

---

## Frontend (Vue.js / TypeScript)

We use **Vue 3 (Composition API)** and **TypeScript**.

### Tools

- **Linter**: `eslint`
- **Type Checker**: `vue-tsc`
- **Formatter**: `prettier`

### TypeScript/Vue Coding Rules

1. **Strict Typing**:
    - **`no-explicit-any` is set to ERROR.** Do not use `any`.
    - Define interfaces or types for all props, emits, and API responses.
    - Use Zod for runtime validation of external data (API responses).

    ```typescript
    // BAD
    const props = defineProps(['user']);

    // GOOD
    interface User {
      id: number;
      name: string;
    }
    const props = defineProps<{ user: User }>();
    ```

2. **Component Structure**:
    - Use `<script setup lang="ts">`.
    - Keep components small and focused (Single Responsibility Principle).
    - Place generic logic in composables (`useSomething.ts`).

3. **Naming Conventions**:
    - **Files**: `PascalCase` for components (`UserProfile.vue`), `camelCase` for utilities/composables (`useAuth.ts`, `formatDate.ts`).
    - **Variables/Functions**: `camelCase`.
    - **Components (in template)**: `PascalCase` (e.g., `<UserProfile />`).

4. **State Management (Pinia)**:
    - Use Setup Stores (function syntax) over Option Stores.
    - Type state, getters, and actions explicitly.

5. **Tailwind CSS**:
    - Use utility classes for styling.
    - Extract common patterns into component classes (`@apply`) or reusable Vue components if repeated significantly.

---

## Git Workflow

1. **Commit Messages**: Use semantic commit messages.
    - `feat: ...` for new features
    - `fix: ...` for bug fixes
    - `refactor: ...` for code restructuring
    - `docs: ...` for documentation
    - `chore: ...` for config/build changes
2. **Branches**:
    - `main`: Production-ready code.
    - `develop` (optional): Integration branch.
    - `feature/your-feature-name`: For new work.
    - `fix/bug-description`: For bug fixes.

---

## Enforcement

These rules are enforced via CI checks.

- **Backend**: `ruff check .` and `mypy .`
- **Frontend**: `npm run lint` and `npm run type-check`

**Do not bypass these checks.**
