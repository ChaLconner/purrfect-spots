-- Migration 042: durable Stripe event idempotency and ordered subscription state.

BEGIN;

-- Billing flags are application invariants, not tri-state values.
UPDATE public.users SET is_pro = false WHERE is_pro IS NULL;
UPDATE public.users SET cancel_at_period_end = false WHERE cancel_at_period_end IS NULL;

ALTER TABLE public.users
    ALTER COLUMN is_pro SET DEFAULT false,
    ALTER COLUMN is_pro SET NOT NULL,
    ALTER COLUMN cancel_at_period_end SET DEFAULT false,
    ALTER COLUMN cancel_at_period_end SET NOT NULL;

-- A customer must map to at most one application account. Existing duplicate
-- rows must be repaired before this migration can complete.
CREATE UNIQUE INDEX IF NOT EXISTS users_stripe_customer_id_key
    ON public.users (stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.stripe_webhook_events (
    event_id text PRIMARY KEY,
    event_type text NOT NULL,
    event_created_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    status text NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'processed', 'failed')),
    attempts integer NOT NULL DEFAULT 1 CHECK (attempts > 0),
    processed_at timestamptz,
    last_error text,
    CONSTRAINT stripe_webhook_events_event_id_not_blank CHECK (btrim(event_id) <> ''),
    CONSTRAINT stripe_webhook_events_event_type_not_blank CHECK (btrim(event_type) <> '')
);

CREATE INDEX IF NOT EXISTS stripe_webhook_events_status_received_idx
    ON public.stripe_webhook_events (status, received_at);

CREATE TABLE IF NOT EXISTS public.stripe_subscriptions (
    stripe_subscription_id text PRIMARY KEY,
    stripe_customer_id text NOT NULL,
    user_id uuid REFERENCES public.users (id) ON DELETE SET NULL,
    status text NOT NULL,
    is_pro_plan boolean NOT NULL DEFAULT false,
    cancel_at_period_end boolean NOT NULL DEFAULT false,
    current_period_end timestamptz,
    event_created_at timestamptz NOT NULL,
    last_event_id text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT stripe_subscriptions_id_not_blank CHECK (btrim(stripe_subscription_id) <> ''),
    CONSTRAINT stripe_subscriptions_customer_not_blank CHECK (btrim(stripe_customer_id) <> ''),
    CONSTRAINT stripe_subscriptions_event_not_blank CHECK (btrim(last_event_id) <> '')
);

CREATE INDEX IF NOT EXISTS stripe_subscriptions_customer_status_idx
    ON public.stripe_subscriptions (stripe_customer_id, status, current_period_end DESC);

ALTER TABLE public.stripe_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stripe_subscriptions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.stripe_webhook_events, public.stripe_subscriptions
    FROM PUBLIC, anon, authenticated;
GRANT ALL ON TABLE public.stripe_webhook_events, public.stripe_subscriptions TO service_role;

-- Claim is atomic. Failed events can be retried; a concurrent processing row
-- is reclaimed only after five minutes to recover from a crashed worker.
CREATE OR REPLACE FUNCTION public.claim_stripe_webhook_event(
    p_event_id text,
    p_event_type text,
    p_event_created_at timestamptz
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_claimed text;
BEGIN
    INSERT INTO public.stripe_webhook_events (
        event_id, event_type, event_created_at, received_at, status, attempts
    ) VALUES (
        p_event_id, p_event_type, p_event_created_at, pg_catalog.now(), 'processing', 1
    )
    ON CONFLICT (event_id) DO UPDATE
    SET received_at = pg_catalog.now(),
        status = 'processing',
        attempts = public.stripe_webhook_events.attempts + 1,
        last_error = NULL
    WHERE public.stripe_webhook_events.status = 'failed'
       OR (
           public.stripe_webhook_events.status = 'processing'
           AND public.stripe_webhook_events.received_at < pg_catalog.now() - interval '5 minutes'
       )
    RETURNING event_id INTO v_claimed;

    RETURN jsonb_build_object('claimed', v_claimed IS NOT NULL);
END;
$$;

CREATE OR REPLACE FUNCTION public.complete_stripe_webhook_event(p_event_id text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_updated integer;
BEGIN
    UPDATE public.stripe_webhook_events
    SET status = 'processed', processed_at = pg_catalog.now(), last_error = NULL
    WHERE event_id = p_event_id AND status <> 'processed';
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN jsonb_build_object('completed', v_updated = 1);
END;
$$;

CREATE OR REPLACE FUNCTION public.fail_stripe_webhook_event(p_event_id text, p_error text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_updated integer;
BEGIN
    UPDATE public.stripe_webhook_events
    SET status = 'failed', last_error = left(p_error, 1000)
    WHERE event_id = p_event_id AND status = 'processing';
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN jsonb_build_object('failed', v_updated = 1);
END;
$$;

-- Store a subscription snapshot only when its Stripe event is newer. Then
-- derive account entitlement from every live Pro subscription for the customer;
-- an old subscription deletion cannot revoke a newer subscription.
CREATE OR REPLACE FUNCTION public.apply_stripe_subscription_event(
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
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_applied boolean := false;
    v_user_id uuid;
    v_live_end timestamptz;
    v_live_cancel boolean;
    v_is_pro boolean := false;
BEGIN
    INSERT INTO public.stripe_subscriptions (
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
    ) VALUES (
        p_subscription_id,
        p_customer_id,
        p_user_id,
        p_status,
        COALESCE(p_is_pro_plan, false),
        COALESCE(p_cancel_at_period_end, false),
        p_current_period_end,
        p_event_created_at,
        p_event_id,
        pg_catalog.now()
    )
    ON CONFLICT (stripe_subscription_id) DO UPDATE
    SET stripe_customer_id = EXCLUDED.stripe_customer_id,
        user_id = COALESCE(EXCLUDED.user_id, public.stripe_subscriptions.user_id),
        status = EXCLUDED.status,
        is_pro_plan = EXCLUDED.is_pro_plan,
        cancel_at_period_end = EXCLUDED.cancel_at_period_end,
        current_period_end = EXCLUDED.current_period_end,
        event_created_at = EXCLUDED.event_created_at,
        last_event_id = EXCLUDED.last_event_id,
        updated_at = pg_catalog.now()
    WHERE public.stripe_subscriptions.event_created_at < EXCLUDED.event_created_at
       OR (
           public.stripe_subscriptions.event_created_at = EXCLUDED.event_created_at
           AND public.stripe_subscriptions.last_event_id < EXCLUDED.last_event_id
       )
    RETURNING true INTO v_applied;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('applied', false, 'user_found', true);
    END IF;

    SELECT u.id
    INTO v_user_id
    FROM public.users AS u
    WHERE u.stripe_customer_id = p_customer_id
    LIMIT 1;

    IF v_user_id IS NULL AND p_user_id IS NOT NULL THEN
        SELECT u.id
        INTO v_user_id
        FROM public.users AS u
        WHERE u.id = p_user_id
          AND (u.stripe_customer_id IS NULL OR u.stripe_customer_id = p_customer_id)
        LIMIT 1;
    END IF;

    IF v_user_id IS NULL THEN
        RETURN jsonb_build_object('applied', v_applied, 'user_found', false);
    END IF;

    UPDATE public.users
    SET stripe_customer_id = p_customer_id,
        updated_at = pg_catalog.now()
    WHERE id = v_user_id
      AND (stripe_customer_id IS NULL OR stripe_customer_id = p_customer_id);

    SELECT s.current_period_end, s.cancel_at_period_end
    INTO v_live_end, v_live_cancel
    FROM public.stripe_subscriptions AS s
    WHERE s.stripe_customer_id = p_customer_id
      AND s.is_pro_plan IS TRUE
      AND (
          s.status IN ('active', 'trialing')
          OR (s.status = 'past_due' AND s.current_period_end > pg_catalog.now())
      )
    ORDER BY s.current_period_end DESC NULLS LAST, s.event_created_at DESC
    LIMIT 1;

    IF FOUND THEN
        v_is_pro := true;
        UPDATE public.users
        SET is_pro = true,
            subscription_end_date = v_live_end,
            cancel_at_period_end = COALESCE(v_live_cancel, false),
            updated_at = pg_catalog.now()
        WHERE id = v_user_id;
    ELSE
        UPDATE public.users
        SET is_pro = false,
            subscription_end_date = NULL,
            cancel_at_period_end = false,
            updated_at = pg_catalog.now()
        WHERE id = v_user_id;
    END IF;

    RETURN jsonb_build_object('applied', v_applied, 'user_found', true, 'is_pro', v_is_pro);
END;
$$;

REVOKE ALL ON FUNCTION public.claim_stripe_webhook_event(text, text, timestamptz)
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.complete_stripe_webhook_event(text)
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.fail_stripe_webhook_event(text, text)
    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.apply_stripe_subscription_event(text, text, uuid, text, boolean, boolean, timestamptz, text, timestamptz)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_stripe_webhook_event(text, text, timestamptz) TO service_role;
GRANT EXECUTE ON FUNCTION public.complete_stripe_webhook_event(text) TO service_role;
GRANT EXECUTE ON FUNCTION public.fail_stripe_webhook_event(text, text) TO service_role;
GRANT EXECUTE ON FUNCTION public.apply_stripe_subscription_event(text, text, uuid, text, boolean, boolean, timestamptz, text, timestamptz) TO service_role;

COMMIT;
