-- Add schedule_date column to attendance_events table
ALTER TABLE attendance_events 
ADD COLUMN IF NOT EXISTS schedule_date TIMESTAMP;
