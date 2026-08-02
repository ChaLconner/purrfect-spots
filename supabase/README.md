# Supabase migrations

`supabase/migrations/` is the canonical location for all new database changes.
Create new files with `supabase migration new <name>`, validate with
`supabase db reset`, then inspect `supabase db push --dry-run` before pushing.

The hosted project predates this directory and contains historical migrations
that are not fully represented in Git. The legacy SQL files under
`backend/migrations/` and `backend/supabase/migrations/` remain reference-only;
do not edit or replay them as a batch.

The first migration synchronized between this directory and production is:

- `20260729100925_harden_database_security.sql`

Do not use `supabase migration repair` to mark missing historical files as
applied unless the remote schema has first been dumped and reviewed.
