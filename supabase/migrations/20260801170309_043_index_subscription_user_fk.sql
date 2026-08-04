begin;

create index if not exists stripe_subscriptions_user_id_idx
  on public.stripe_subscriptions (user_id);

commit;
