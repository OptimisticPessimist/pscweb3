from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.dependencies.auth import get_current_user_dep
from src.db import get_db
from src.db.models import User, ProjectMember, Project, RehearsalSchedule, Rehearsal, Milestone
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()


class MyScheduleEvent(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime | None
    type: str  # "rehearsal" or "milestone"
    project_id: str
    project_name: str
    project_color: str
    location: str | None = None
    notes: str | None = None
    scene_heading: str | None = None


class MyScheduleResponse(BaseModel):
    events: List[MyScheduleEvent]


@router.get("/my-schedule", response_model=MyScheduleResponse)
async def get_my_schedule(
    current_user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all rehearsals and milestones for all projects the user is a member of.
    """
    # 1. Get all projects the user is a member of
    stmt = select(ProjectMember).where(
        ProjectMember.user_id == current_user.id
    ).options(
        selectinload(ProjectMember.project)
    )
    result = await db.execute(stmt)
    memberships = result.scalars().all()
    
    project_ids = [m.project_id for m in memberships]
    
    if not project_ids:
        return MyScheduleResponse(events=[])
    
    # プロジェクトごとの色を定義（プロジェクトIDのハッシュベース）
    colors = [
        '#3b82f6',  # blue-500
        '#10b981',  # green-500
        '#f59e0b',  # amber-500
        '#ef4444',  # red-500
        '#8b5cf6',  # purple-500
        '#ec4899',  # pink-500
        '#06b6d4',  # cyan-500
    ]
    
    events = []
    
    # 2. Get all rehearsals from all projects
    for idx, membership in enumerate(memberships):
        project = membership.project
        project_color = colors[idx % len(colors)]
        
        # Get rehearsals for this project
        schedule_stmt = select(RehearsalSchedule).where(
            RehearsalSchedule.project_id == project.id
        ).options(
            selectinload(RehearsalSchedule.rehearsals)
        )
        schedule_result = await db.execute(schedule_stmt)
        schedule = schedule_result.scalar_one_or_none()
        
        if schedule and schedule.rehearsals:
            for rehearsal in schedule.rehearsals:
                end_time = rehearsal.date + timedelta(minutes=rehearsal.duration_minutes) if rehearsal.duration_minutes else None
                events.append(MyScheduleEvent(
                    id=f"rehearsal-{rehearsal.id}",
                    title=f"{rehearsal.scene_heading or 'Rehearsal'} ({project.name})",
                    start=rehearsal.date,
                    end=end_time,
                    type="rehearsal",
                    project_id=project.id,
                    project_name=project.name,
                    project_color=project_color,
                    location=rehearsal.location,
                    notes=rehearsal.notes,
                    scene_heading=rehearsal.scene_heading
                ))
        
        # Get milestones for this project
        milestone_stmt = select(Milestone).where(
            Milestone.project_id == project.id
        )
        milestone_result = await db.execute(milestone_stmt)
        milestones = milestone_result.scalars().all()
        
        for milestone in milestones:
            events.append(MyScheduleEvent(
                id=f"milestone-{milestone.id}",
                title=f"{milestone.title} ({project.name})",
                start=milestone.start_date,
                end=milestone.end_date,
                type="milestone",
                project_id=project.id,
                project_name=project.name,
                project_color=project_color,
                location=milestone.location,
                notes=milestone.description
            ))
    
    return MyScheduleResponse(events=events)
