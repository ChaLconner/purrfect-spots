-- Remove the legacy four-argument overload. Its default amount parameter lets
-- untyped three-argument calls become ambiguous with the canonical RPC.
begin;

drop function if exists public.give_treat_atomic(uuid, uuid, uuid, integer);

commit;
