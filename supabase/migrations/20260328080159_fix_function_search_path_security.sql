-- PHASE 3: FUNCTION SECURITY (Fixed search_path for SECURITY DEFINER functions)

ALTER FUNCTION public.audit_trigger_func() SET search_path = public, pg_temp;
ALTER FUNCTION public.get_admin_trends(days_back integer) SET search_path = public, pg_temp;
ALTER FUNCTION public.get_monthly_report(report_year integer) SET search_path = public, pg_temp;
ALTER FUNCTION public.users_search_vector_trigger() SET search_path = public, pg_temp;

-- Ensure handle_new_user also has pg_temp
ALTER FUNCTION public.handle_new_user() SET search_path = public, pg_temp;

