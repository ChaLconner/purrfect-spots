-- 1. Add new columns to system_configs
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_configs' AND column_name='category') THEN
        ALTER TABLE public.system_configs ADD COLUMN category TEXT DEFAULT 'general';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_configs' AND column_name='is_encrypted') THEN
        ALTER TABLE public.system_configs ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_configs' AND column_name='requires_approval') THEN
        ALTER TABLE public.system_configs ADD COLUMN requires_approval BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_configs' AND column_name='updated_by') THEN
        ALTER TABLE public.system_configs ADD COLUMN updated_by UUID REFERENCES public.users(id);
    END IF;
END $$;

-- 2. Create config_history table
CREATE TABLE IF NOT EXISTS public.config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR REFERENCES public.system_configs(key),
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES public.users(id),
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create pending_config_changes table for Approval Workflow
CREATE TABLE IF NOT EXISTS public.pending_config_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR REFERENCES public.system_configs(key),
    proposed_value JSONB,
    requester_id UUID REFERENCES public.users(id),
    approver_id UUID REFERENCES public.users(id),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for new tables
ALTER TABLE public.config_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_config_changes ENABLE ROW LEVEL SECURITY;

-- Add some initial data if empty to test categories
INSERT INTO public.system_configs (key, value, type, category, description, is_public)
VALUES 
('site_name', '"Purrfect Spots"', 'string', 'general', 'ชื่อเว็บไซต์หลัก', true),
('maintenance_mode', 'false', 'boolean', 'general', 'โหมดปรับปรุงระบบ', true),
('max_upload_size_mb', '10', 'integer', 'infrastructure', 'ขนาดไฟล์สูงสุด (MB)', false),
('session_timeout_minutes', '60', 'integer', 'security', 'ระยะเวลา Session (นาที)', false),
('privacy_policy_version', '"1.0.0"', 'string', 'pdpa', 'เวอร์ชันนโยบายความเป็นส่วนตัว', true)
ON CONFLICT (key) DO UPDATE 
SET category = EXCLUDED.category,
    description = EXCLUDED.description;

