# Project Structure

Purrfect Spots is a monorepo with explicit application, deployment, generated-code, and infrastructure boundaries.

## Repository Layout

```text
.
├── .github/                 # CI, release, ownership, and repository automation
├── .husky/                  # Local Git hooks
├── backend/
│   ├── app/                 # Importable FastAPI application package
│   │   ├── constants/
│   │   ├── middleware/
│   │   ├── routes/          # HTTP controller layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Background task definitions
│   │   └── utils/           # Stateless shared helpers
│   ├── api/                 # Serverless deployment adapter
│   ├── migrations/          # Historical reference migrations
│   ├── scripts/             # Backend maintenance and generation commands
│   ├── supabase/            # Historical Supabase migration reference
│   └── tests/               # Unit, integration, and performance tests
├── docs/                    # Architecture, standards, operations, and API baseline
├── frontend/
│   ├── e2e/                 # Playwright tests
│   ├── public/              # Static public assets
│   ├── src/
│   │   ├── components/      # Reusable components grouped by domain
│   │   │   └── ui/          # Domain-neutral design-system components
│   │   ├── composables/     # Reusable stateful Vue logic
│   │   ├── generated/       # Generated API contracts; never edit manually
│   │   ├── router/          # Route definitions and guards
│   │   ├── services/        # External and backend API boundaries
│   │   ├── stores/          # Pinia stores
│   │   ├── types/           # Hand-written domain types
│   │   ├── utils/           # Stateless helpers
│   │   └── views/           # Route-level components
│   └── tests/               # Vitest tests mirroring source concerns
├── packages/
│   └── api-client/          # OpenAPI client generator package
└── supabase/
    └── migrations/          # Canonical location for new Supabase migrations
```

## Dependency Rules

### Backend

- Import application code through `app.*`.
- Routes validate HTTP input and delegate business behavior to services.
- Services must not depend on FastAPI request or response objects.
- Schemas contain transport contracts, not database access.
- Utilities stay stateless. Stateful integrations belong in services or dedicated clients.
- `api/` may import `app`, but `app` must not import deployment adapters.
- Tests may import `app`; production code must never import `tests` or `scripts`.

### Frontend

- Views compose domain components and route-specific behavior.
- Domain components stay in named component folders. Only generic primitives belong in `components/ui/`.
- Shared state belongs in `stores/`; reusable stateful logic belongs in `composables/`.
- API and third-party calls belong in `services/`.
- `generated/` is replaced by generators. Hand-written types stay in `types/`.
- Tests mirror source domains and import source through the `@/` alias.

## Database Migration Safety

`supabase/migrations/` is canonical for new migrations. Historical files in `backend/migrations/` and `backend/supabase/migrations/` remain reference-only because deployed migration identity predates the current Supabase CLI layout. Do not rename, replay, or consolidate them without comparing remote migration history and a reviewed schema dump.

## Local and Generated Artifacts

Dependency directories, virtual environments, caches, logs, test reports, local build output, and pre-audit backups are not source structure. Keep them ignored and outside imports. Do not commit them.

## Required Validation After Structural Changes

```bash
cd backend
python -m pytest
ruff check app tests scripts
mypy app

cd ../frontend
npm run lint:check
npm run type-check
npm test
npm run build
```

