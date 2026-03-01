# Purrfect Spots Git & Commit Guidelines

To maintain a clean and traceable project history, we follow strict Git and Commit standards. These rules are enforced via CI/CD and pre-commit hooks.

## 1. Commit Message Format (Conventional Commits)

We use the **Conventional Commits** specification. Every commit message must follow this structure:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Allowed Types

- **feat**: A new feature for the user.
- **fix**: A bug fix.
- **docs**: Documentation only changes.
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
- **refactor**: A code change that neither fixes a bug nor adds a feature.
- **perf**: A code change that improves performance.
- **test**: Adding missing tests or correcting existing tests.
- **build**: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm).
- **ci**: Changes to our CI configuration files and scripts (example scopes: GitHub Actions, Travis, Circle, BrowserStack, SauceLabs).
- **chore**: Other changes that don't modify src or test files.
- **revert**: Reverts a previous commit.

### Best Practices

- **Imperative Mood**: Use "fix", not "fixed" or "fixes".
- **Lowercase Description**: Start the description with a lowercase letter.
- **No Period at End**: Do not end the description line with a period.
- **Scope (Optional)**: Provide a scope to specify the part of the codebase affected (e.g., `feat(api):`, `fix(ui):`).
- **Breaking Changes**: Indicate breaking changes by adding a `!` after the type/scope or adding `BREAKING CHANGE:` in the footer.

**Bad Example:**

```text
fixed the bug in login and updated css
```

**Good Example:**

```text
fix(auth): correct password validation logic and update login styles
```

---

## 2. Branching Strategy

- **`main`**: Production-ready code. No direct pushes allowed.
- **`dev` / `develop`**: Integration branch for features.
- **`feature/*`**: New features (e.g., `feature/add-oauth-support`).
- **`fix/*`**: Bug fixes (e.g., `fix/header-mobile-padding`).
- **`hotfix/*`**: Emergency fixes for production.

---

## 3. Pull Request (PR) Rules

1. **Atomic Commits**: Each commit should represent one logical change.
2. **No Direct Pushes**: All changes to `main` and `dev` must go through a PR.
3. **Link to Issue**: Every PR must be linked to a GitHub Issue (e.g., `Closes #123`).
4. **CI/CD Compliance**: All status checks must pass (Lint, Tests, Security Scans).
5. **Review Requirement**: At least **1 Reviewer Approval** is required.
6. **Squash & Merge**: Preferred for feature branches to keep `main` history clean.

---

## 4. Local Hooks

We use **Husky** and **lint-staged** to ensure code quality before it reaches the repository.

- **Pre-commit**: Runs linters and tests.
- **Commit-msg**: (Optional/Recommended) Use a tool like `commitlint` to enforce message format.
