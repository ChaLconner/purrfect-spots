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

Migration version prefixes are part of the migration identity. For migrations
already applied after that synchronization point, the local filename must use
the exact remote version; do not create a second copy under a new timestamp.
Review the remote schema before restoring a missing file, then validate with
`supabase db push --dry-run`.

Do not use `supabase migration repair` to mark missing historical files as
applied unless the remote schema has first been dumped and reviewed.
Only the migrations shown by the dry-run as pending should be applied. If
history drift recurs, dump and review the remote schema before using
`supabase migration repair`.
