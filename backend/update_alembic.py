import os
import re

p = 'alembic/versions/507f4dcf6072_add_attendance_reminder_hours_config.py'

with open(p, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "op.add_column('theater_projects', sa.Column('attendance_reminder_hours', sa.Integer(), nullable=False))",
    "op.add_column('theater_projects', sa.Column('attendance_reminder_hours', sa.Integer(), nullable=False, server_default=sa.text('24')))"
)
text = text.replace(
    "op.add_column('theater_projects', sa.Column('attendance_deadline_reminder_hours', sa.Integer(), nullable=False))",
    "op.add_column('theater_projects', sa.Column('attendance_deadline_reminder_hours', sa.Integer(), nullable=False, server_default=sa.text('24')))"
)

with open(p, 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Alembic migration.")
