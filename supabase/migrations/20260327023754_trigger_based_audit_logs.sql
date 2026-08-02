
-- Create the audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_user_id uuid;
    v_action text;
    v_resource text;
    v_changes jsonb;
BEGIN
    v_resource := TG_TABLE_NAME;
    
    IF (TG_OP = 'INSERT') THEN
        v_action := 'CREATE_' || UPPER(v_resource);
        v_changes := to_jsonb(NEW);
    ELSIF (TG_OP = 'UPDATE') THEN
        v_action := 'UPDATE_' || UPPER(v_resource);
        -- Basic delta: only include columns that changed
        v_changes := (to_jsonb(NEW) - 'updated_at') || jsonb_build_object('_old', to_jsonb(OLD) - 'updated_at');
    ELSIF (TG_OP = 'DELETE') THEN
        v_action := 'DELETE_' || UPPER(v_resource);
        v_changes := to_jsonb(OLD);
    END IF;

    -- Attempt to get current user ID from Supabase auth.uid() or similar context if available
    -- Note: Since we are calling from a service role with admin privileges, we often rely 
    -- on the application to pass user info via GUC if we wanted 100% DB-only automation.
    -- For now, we will log what the DB sees.
    
    INSERT INTO audit_logs (
        user_id, 
        action, 
        resource, 
        changes, 
        ip_address, 
        user_agent
    ) VALUES (
        COALESCE(auth.uid(), '00000000-0000-0000-0000-000000000000'::uuid), -- System/Admin ID if no auth context
        v_action,
        v_resource,
        v_changes,
        'database_trigger',
        'postgresql_internal'
    );

    RETURN NULL; -- result is ignored since this is an AFTER trigger
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply to critical tables
DROP TRIGGER IF EXISTS audit_system_configs_trigger ON system_configs;
CREATE TRIGGER audit_system_configs_trigger
AFTER INSERT OR UPDATE OR DELETE ON system_configs
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

DROP TRIGGER IF EXISTS audit_roles_trigger ON roles;
CREATE TRIGGER audit_roles_trigger
AFTER INSERT OR UPDATE OR DELETE ON roles
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

