-- Function to automatically create a profile in public.users when a new user signs up via Supabase Auth
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
        name = excluded.name;
  end if;
  return new;
end;
$$;

-- Trigger the function every time a user is created
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Trigger for updates (optional, to keep email synced)
drop trigger if exists on_auth_user_updated on auth.users;
create trigger on_auth_user_updated
  after update on auth.users
  for each row execute procedure public.handle_new_user();
