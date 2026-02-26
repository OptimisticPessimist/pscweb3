-- Add required_roles to schedule_polls
ALTER TABLE schedule_polls ADD COLUMN IF NOT EXISTS required_roles TEXT;
