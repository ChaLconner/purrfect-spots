# Purrfect Spots Documentation

Canonical project documentation. Start here instead of searching individual
files.

## Architecture

- [System architecture](./architecture/ARCHITECTURE.md) - Runtime components
  and service boundaries.
- [Project structure](./architecture/PROJECT_STRUCTURE.md) - Folder ownership
  and dependency rules.

## Development

- [Coding standards](./development/CODING_STANDARDS.md) - Enforced project
  conventions.
- [Git guidelines](./development/GIT_GUIDELINES.md) - Branch, commit, and PR
  rules.
- [Design tokens](./development/DESIGN_TOKENS.md) - UI tokens and component
  styling.

## Reference

- [OpenAPI baseline](./openapi-baseline.json) - Machine-readable API contract
  used by validation and client generation.

## Sources of truth

- Environment variables: [root](../.env.example),
  [frontend](../frontend/.env.example), and
  [backend](../backend/.env.example) templates.
- Database state: [canonical Supabase migrations](../supabase/migrations/) plus
  historical migration locations described in
  [Project structure](./architecture/PROJECT_STRUCTURE.md).
- Deployment: [deploy workflow](../.github/workflows/deploy.yml).
- Runtime health endpoints: [health routes](../backend/app/routes/health.py).
- Release history: [release workflow](../.github/workflows/release.yml) and
  repository releases.

## Maintenance policy

- Keep one canonical document per topic.
- Put design and coding rules in `development/`; system descriptions in
  `architecture/`.
- Keep generated or machine-consumed artifacts at stable paths unless every
  consumer changes in the same commit.
- Link to executable configuration instead of copying environment, database,
  deployment, or operational details into manually maintained documents.
- Use Git history for obsolete documents. Do not keep an `archive/` directory.
- Update this index and all inbound links when moving a document.
