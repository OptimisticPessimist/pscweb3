-- Add public_terms and public_contact columns to scripts table
ALTER TABLE scripts ADD COLUMN IF NOT EXISTS public_terms TEXT;
ALTER TABLE scripts ADD COLUMN IF NOT EXISTS public_contact VARCHAR(200);
