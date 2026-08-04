begin;

create or replace function public.apply_stripe_subscription_event(
    p_subscription_id text,
    p_customer_id text,
    p_user_id uuid,
    p_status text,
    p_is_pro_plan boolean,
    p_cancel_at_period_end boolean,
    p_current_period_end timestamptz,
    p_event_id text,
    p_event_created_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_applied boolean := false;
    v_user_id uuid;
    v_live_end timestamptz;
    v_live_cancel boolean;
    v_is_pro boolean := false;
begin
    insert into public.stripe_subscriptions (
        stripe_subscription_id,
        stripe_customer_id,
        user_id,
        status,
        is_pro_plan,
        cancel_at_period_end,
        current_period_end,
        event_created_at,
        last_event_id,
        updated_at
    ) values (
        p_subscription_id,
        p_customer_id,
        p_user_id,
        p_status,
        coalesce(p_is_pro_plan, false) and p_current_period_end is not null,
        coalesce(p_cancel_at_period_end, false),
        p_current_period_end,
        p_event_created_at,
        p_event_id,
        pg_catalog.now()
    )
    on conflict (stripe_subscription_id) do update
    set stripe_customer_id = excluded.stripe_customer_id,
        user_id = coalesce(excluded.user_id, public.stripe_subscriptions.user_id),
        status = excluded.status,
        is_pro_plan = excluded.is_pro_plan,
        cancel_at_period_end = excluded.cancel_at_period_end,
        current_period_end = excluded.current_period_end,
        event_created_at = excluded.event_created_at,
        last_event_id = excluded.last_event_id,
        updated_at = pg_catalog.now()
    where public.stripe_subscriptions.event_created_at < excluded.event_created_at
       or (
           public.stripe_subscriptions.event_created_at = excluded.event_created_at
           and public.stripe_subscriptions.last_event_id < excluded.last_event_id
       )
    returning true into v_applied;

    if not found then
        return jsonb_build_object('applied', false, 'user_found', true);
    end if;

    select u.id into v_user_id
    from public.users as u
    where u.stripe_customer_id = p_customer_id
    limit 1;

    if v_user_id is null and p_user_id is not null then
        select u.id into v_user_id
        from public.users as u
        where u.id = p_user_id
          and (u.stripe_customer_id is null or u.stripe_customer_id = p_customer_id)
        limit 1;
    end if;

    if v_user_id is null then
        return jsonb_build_object('applied', v_applied, 'user_found', false);
    end if;

    update public.users
    set stripe_customer_id = p_customer_id, updated_at = pg_catalog.now()
    where id = v_user_id
      and (stripe_customer_id is null or stripe_customer_id = p_customer_id);

    select s.current_period_end, s.cancel_at_period_end
    into v_live_end, v_live_cancel
    from public.stripe_subscriptions as s
    where s.stripe_customer_id = p_customer_id
      and s.is_pro_plan is true
      and (
          (s.status in ('active', 'trialing') and s.current_period_end is not null)
          or (s.status = 'past_due' and s.current_period_end > pg_catalog.now())
      )
    order by s.current_period_end desc nulls last, s.event_created_at desc
    limit 1;

    if found then
        v_is_pro := true;
        update public.users
        set is_pro = true,
            subscription_end_date = v_live_end,
            cancel_at_period_end = coalesce(v_live_cancel, false),
            updated_at = pg_catalog.now()
        where id = v_user_id;
    else
        update public.users
        set is_pro = false,
            subscription_end_date = null,
            cancel_at_period_end = false,
            updated_at = pg_catalog.now()
        where id = v_user_id;
    end if;

    return jsonb_build_object('applied', v_applied, 'user_found', true, 'is_pro', v_is_pro);
end;
$$;

revoke all on function public.apply_stripe_subscription_event(text, text, uuid, text, boolean, boolean, timestamptz, text, timestamptz)
    from public, anon, authenticated;
grant execute on function public.apply_stripe_subscription_event(text, text, uuid, text, boolean, boolean, timestamptz, text, timestamptz)
    to service_role;

commit;
