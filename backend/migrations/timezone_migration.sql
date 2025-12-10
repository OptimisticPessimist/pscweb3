-- ===================================
-- データベース完全リセット + タイムゾーン対応
-- ===================================

-- 1. 全データ削除（外部キー制約を考慮した順序）
TRUNCATE TABLE 
  scene_character_mappings,
  rehearsal_casts,
  rehearsal_participants,
  character_castings,
  attendance_targets,
  lines,
  rehearsals,
  scenes,
  characters,
  scene_charts,
  scripts,
  rehearsal_schedules,
  attendance_events,
  milestones,
  project_invitations,
  audit_logs,
  notification_settings,
  project_members,
  theater_projects,
  users
CASCADE;

-- 2. タイムゾーン対応マイグレーション

-- users
ALTER TABLE users 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- theater_projects
ALTER TABLE theater_projects 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- project_members
ALTER TABLE project_members 
  ALTER COLUMN joined_at TYPE TIMESTAMP WITH TIME ZONE 
  USING joined_at AT TIME ZONE 'UTC';

-- scripts
ALTER TABLE scripts 
  ALTER COLUMN uploaded_at TYPE TIMESTAMP WITH TIME ZONE 
  USING uploaded_at AT TIME ZONE 'UTC';

-- scene_charts
ALTER TABLE scene_charts 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
  USING updated_at AT TIME ZONE 'UTC';

-- rehearsal_schedules
ALTER TABLE rehearsal_schedules 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- rehearsals（最重要）
ALTER TABLE rehearsals 
  ALTER COLUMN date TYPE TIMESTAMP WITH TIME ZONE 
  USING date AT TIME ZONE 'UTC';

-- project_invitations
ALTER TABLE project_invitations 
  ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE 
  USING expires_at AT TIME ZONE 'UTC',
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- audit_logs
ALTER TABLE audit_logs 
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- milestones
ALTER TABLE milestones 
  ALTER COLUMN start_date TYPE TIMESTAMP WITH TIME ZONE 
  USING start_date AT TIME ZONE 'UTC';

-- milestones end_date (NULLableのため個別に)
ALTER TABLE milestones 
  ALTER COLUMN end_date TYPE TIMESTAMP WITH TIME ZONE 
  USING CASE WHEN end_date IS NOT NULL THEN end_date AT TIME ZONE 'UTC' ELSE NULL END;

-- attendance_events
ALTER TABLE attendance_events 
  ALTER COLUMN deadline TYPE TIMESTAMP WITH TIME ZONE 
  USING deadline AT TIME ZONE 'UTC',
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
  USING created_at AT TIME ZONE 'UTC';

-- attendance_events schedule_date (NULLableのため個別に)
ALTER TABLE attendance_events 
  ALTER COLUMN schedule_date TYPE TIMESTAMP WITH TIME ZONE 
  USING CASE WHEN schedule_date IS NOT NULL THEN schedule_date AT TIME ZONE 'UTC' ELSE NULL END;
