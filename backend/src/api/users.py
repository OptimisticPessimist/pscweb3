"""ユーザーAPIエンドポイント."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from src.auth.jwt import get_current_user
from src.db import get_db
from src.db.models import Rehearsal, RehearsalParticipant, RehearsalCast, Milestone, ProjectMember, TheaterProject, RehearsalSchedule
from src.schemas.auth import UserResponse
from src.schemas.schedule import UserScheduleResponse, ScheduleItem

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """現在のユーザー情報を取得.

    Args:
        authorization: Authorization header (Bearer <token>)
        db: データベースセッション

    Returns:
        UserResponse: ユーザー情報

    Raises:
        HTTPException: 認証エラー
    """
    if not authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token = authorization.split(" ")[1]
    
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="無効なトークンです")

    return UserResponse.model_validate(user)


@router.get("/me/schedule", response_model=UserScheduleResponse)
async def get_my_schedule(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db)
) -> UserScheduleResponse:
    """自分のスケジュール（稽古・マイルストーン）を取得."""
    if not authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token = authorization.split(" ")[1]
    user = await get_current_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="無効なトークンです")

    # 1. 稽古の取得
    # 参加者またはキャストとして登録されている稽古
    rehearsal_stmt = (
        select(Rehearsal)
        .join(Rehearsal.schedule)
        .join(TheaterProject, RehearsalSchedule.project_id == TheaterProject.id)
        .outerjoin(RehearsalParticipant, Rehearsal.id == RehearsalParticipant.rehearsal_id)
        .outerjoin(RehearsalCast, Rehearsal.id == RehearsalCast.rehearsal_id)
        .options(
            selectinload(Rehearsal.schedule).selectinload(RehearsalSchedule.project),
            selectinload(Rehearsal.scene)
        )
        .where(
            or_(
                RehearsalParticipant.user_id == user.id,
                RehearsalCast.user_id == user.id
            )
        )
        .distinct()
    )
    # RehearsalSchedule is needed for project link.
    # Note: Rehearsal has `schedule` relationship, Schedule has `project`.
    
    # Wait, I need to check Rehearsal model for relationships.
    # Rehearsal -> Schedule -> Project.
    # Rehearsal.schedule is Mapped[RehearsalSchedule]. RehearsalSchedule.project is Mapped[TheaterProject].
    
    # Updating stmt to be correct with models
    
    # 2. マイルストーンの取得
    # 所属しているプロジェクトのマイルストーン
    milestone_stmt = (
        select(Milestone)
        .join(TheaterProject, Milestone.project_id == TheaterProject.id)
        .join(ProjectMember, TheaterProject.id == ProjectMember.project_id)
        .where(ProjectMember.user_id == user.id)
        .options(selectinload(Milestone.project))
    )

    # Execute queries
    rehearsals_result = await db.execute(rehearsal_stmt)
    rehearsals = rehearsals_result.scalars().all()

    milestones_result = await db.execute(milestone_stmt)
    milestones = milestones_result.scalars().all()

    items = []

    for r in rehearsals:
        project = r.schedule.project
        # End date calculation: date + duration_minutes
        end_date = r.date + timedelta(minutes=r.duration_minutes)
        
        items.append(ScheduleItem(
            id=r.id,
            type="rehearsal",
            title=f"Rehearsal: {r.scene.heading if r.scene else 'No Scene'}",
            date=r.date,
            end_date=end_date,
            project_id=project.id,
            project_name=project.name,
            description=r.notes,
            location=r.location,
            scene_heading=r.scene.heading if r.scene else None
        ))

    for m in milestones:
        items.append(ScheduleItem(
            id=m.id,
            type="milestone",
            title=m.title,
            date=m.start_date,
            end_date=m.end_date,
            project_id=m.project.id,
            project_name=m.project.name,
            description=m.description,
            color=m.color
        ))

    # Sort by date
    items.sort(key=lambda x: x.date)

    return UserScheduleResponse(items=items)

