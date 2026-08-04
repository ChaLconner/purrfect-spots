CREATE INDEX IF NOT EXISTS idx_cat_photos_active_uploaded ON public.cat_photos(uploaded_at DESC) WHERE deleted_at IS NULL AND status = 'approved';
