-- Modify handle_new_user to only create public.users profile AFTER email verification

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  -- Check if email is confirmed before interacting with public.users
  if new.email_confirmed_at is not null then
      insert into public.users (id, email, name, picture, created_at, updated_at)
      values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data->>'name', new.raw_user_meta_data->>'full_name', 'New User'),
        coalesce(new.raw_user_meta_data->>'picture', new.raw_user_meta_data->>'avatar_url', ''),
        new.created_at,
        new.updated_at
      )
      on conflict (id) do update set
        email = excluded.email,
        updated_at = excluded.updated_at,
        -- Keep existing name/picture if they exist, or update them? 
        -- Usually we want to sync from auth if auth changes, but user might update profile separately.
        -- For now, let's just ensure the record exists.
        name = excluded.name; 
  end if;
  return new;
end;
$$;
