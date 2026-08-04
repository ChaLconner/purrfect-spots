
ALTER TABLE "public"."cat_photos"
ADD CONSTRAINT "cat_photos_user_id_fkey"
FOREIGN KEY ("user_id")
REFERENCES "public"."users"("id")
ON DELETE CASCADE;

