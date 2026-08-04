-- Keep the local migration history aligned with the remote fix for the
-- SECURITY DEFINER social mutation.

begin;

create or replace function public.toggle_photo_like(
    p_user_id uuid,
    p_photo_id uuid
)
returns table (
    liked boolean,
    likes_count integer
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_photo_id uuid;
    v_exists boolean;
    v_liked boolean;
    v_new_count integer;
begin
    select photo.id
    into v_photo_id
    from public.cat_photos as photo
    where photo.id = p_photo_id
      and photo.deleted_at is null
      and photo.status = 'approved'
    for update;

    if not found then
        raise exception 'Photo not found';
    end if;

    select exists (
        select 1
        from public.photo_likes
        where user_id = p_user_id and photo_id = p_photo_id
    ) into v_exists;

    if v_exists then
        delete from public.photo_likes
        where user_id = p_user_id and photo_id = p_photo_id;
        v_liked := false;
    else
        insert into public.photo_likes (user_id, photo_id)
        values (p_user_id, p_photo_id);
        v_liked := true;
    end if;

    select coalesce(photo.likes_count, 0)
    into v_new_count
    from public.cat_photos as photo
    where photo.id = p_photo_id;

    return query select v_liked, v_new_count;
end;
$$;

revoke execute on function public.toggle_photo_like(uuid, uuid) from public;
grant execute on function public.toggle_photo_like(uuid, uuid) to service_role;

commit;
