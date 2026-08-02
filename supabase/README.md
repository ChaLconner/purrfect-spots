# Supabase migrations

`supabase/migrations/` is the canonical location for all new database changes.
Create new files with `supabase migration new <name>`, validate with
`supabase db reset`, then inspect `supabase db push --dry-run` before pushing.

The hosted project's migration history is synchronized in this directory from
the remote `supabase_migrations.schema_migrations` table. The legacy SQL files
under `backend/migrations/` and `backend/supabase/migrations/` remain
reference-only; do not edit or replay them as a batch.

Before applying new migrations, verify the linked project and inspect the
pending set:

```bash
supabase migration list
supabase db push --dry-run
```

Only the migrations shown by the dry-run as pending should be applied. If
history drift recurs, dump and review the remote schema before using
`supabase migration repair`.
