"""ダッシュボードAPI."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.db.models import (
    AttendanceEvent,
    AttendanceTarget,
    Milestone,
    ProjectMember,
    Rehearsal,
    RehearsalSchedule,
    Script,
)
from src.dependencies.permissions import get_project_member_dep
from src.schemas.dashboard import (
    ActivityItem,
    DashboardResponse,
    MilestoneInfo,
    RehearsalInfo,
)

router = APIRouter()


@router.get("/{project_id}/dashboard", response_model=DashboardResponse)
async def get_project_dashboard(
    project_id: UUID,
    current_member: ProjectMember = Depends(get_project_member_dep),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """プロジェクトダッシュボード情報を取得.
    
    Args:
        project_id: プロジェクトID
        current_member: 現在のプロジェクトメンバー
        db: データベースセッション
        
    Returns:
        DashboardResponse: ダッシュボード情報
    """
    now = datetime.now()  # timezone-naive for database comparison

    # 1. 次回の稽古を取得
    next_rehearsal = None
    rehearsal_stmt = (
        select(Rehearsal)
        .join(RehearsalSchedule)
        .where(
            RehearsalSchedule.project_id == project_id,
            Rehearsal.date >= now
        )
        .order_by(Rehearsal.date)
        .limit(1)
    )
    result = await db.execute(rehearsal_stmt)
    rehearsal = result.scalar_one_or_none()

    if rehearsal:
        next_rehearsal = RehearsalInfo(
            id=rehearsal.id,
            title="稽古",  # シーン情報があれば追加可能
            start_time=rehearsal.date,
            end_time=rehearsal.date,  # duration_minutesから計算可能
            location=rehearsal.location,
        )

    # 2. 次のマイルストーンを取得
    next_milestone = None
    milestone_stmt = (
        select(Milestone)
        .where(
            Milestone.project_id == project_id,
            Milestone.start_date >= now
        )
        .order_by(Milestone.start_date)
        .limit(1)
    )
    result = await db.execute(milestone_stmt)
    milestone = result.scalar_one_or_none()

    if milestone:
        days_until = (milestone.start_date - now).days
        next_milestone = MilestoneInfo(
            id=milestone.id,
            title=milestone.title,
            start_date=milestone.start_date,
            end_date=milestone.end_date,
            location=milestone.location,
            days_until=days_until,
        )

    # 3. 未回答の出欠確認数を取得 (現在のユーザー)
    pending_count_stmt = (
        select(func.count(AttendanceTarget.id))
        .join(AttendanceEvent)
        .where(
            AttendanceEvent.project_id == project_id,
            AttendanceTarget.user_id == current_member.user_id,
            AttendanceTarget.status == "pending"
        )
    )
    result = await db.execute(pending_count_stmt)
    pending_attendance_count = result.scalar_one() or 0

    # 4. メンバー数を取得
    member_count_stmt = select(func.count(ProjectMember.user_id)).where(
        ProjectMember.project_id == project_id
    )
    result = await db.execute(member_count_stmt)
    total_members = result.scalar_one() or 0

    # 5. 最近のアクティビティを取得 (脚本アップロードなど)
    recent_activities = []
    script_stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .order_by(Script.uploaded_at.desc())
        .limit(5)
    )
    result = await db.execute(script_stmt)
    scripts = result.scalars().all()

    for script in scripts:
        recent_activities.append(
            ActivityItem(
                type="script_upload",
                title=f"脚本「{script.title}」アップロード",
                description=f"Rev.{script.revision}",
                timestamp=script.uploaded_at,
            )
        )

    return DashboardResponse(
        next_rehearsal=next_rehearsal,
        next_milestone=next_milestone,
        pending_attendance_count=pending_attendance_count,
        total_members=total_members,
        recent_activities=recent_activities,
    )
