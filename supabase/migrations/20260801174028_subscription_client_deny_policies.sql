begin;

drop policy if exists stripe_subscriptions_no_client_access on public.stripe_subscriptions;
create policy stripe_subscriptions_no_client_access
on public.stripe_subscriptions
for all
to anon, authenticated
using (false)
with check (false);

drop policy if exists stripe_webhook_events_no_client_access on public.stripe_webhook_events;
create policy stripe_webhook_events_no_client_access
on public.stripe_webhook_events
for all
to anon, authenticated
using (false)
with check (false);

commit;
