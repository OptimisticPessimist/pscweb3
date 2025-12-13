-- Add is_public column to theater_projects table
ALTER TABLE theater_projects ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
