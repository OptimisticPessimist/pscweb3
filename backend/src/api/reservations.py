import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.db.models import Reservation, User, Milestone, TheaterProject, ProjectMember, CharacterCasting
from src.schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from src.services.email import email_service
from src.dependencies.auth import get_current_user_dep as get_current_user, get_optional_current_user_dep as get_current_user_optional
from src.schemas.project import MilestoneResponse

router = APIRouter()

# --- Public API ---

@router.post("/public/reservations", response_model=ReservationResponse)
async def create_reservation(
    reservation: ReservationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """予約作成 (Public)."""
    # マイルストーン取得
    milestone = await db.scalar(select(Milestone).where(Milestone.id == reservation.milestone_id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # 定員チェック
    if milestone.reservation_capacity is not None:
        result = await db.scalar(
            select(func.sum(Reservation.count))
            .where(Reservation.milestone_id == reservation.milestone_id)
        )
        current_count = result or 0
        if current_count + reservation.count > milestone.reservation_capacity:
            raise HTTPException(status_code=400, detail="Reservation capacity exceeded")

    # 予約作成
    db_reservation = Reservation(
        milestone_id=reservation.milestone_id,
        referral_user_id=reservation.referral_user_id,
        user_id=current_user.id if current_user else None,
        name=reservation.name,
        email=reservation.email,
        count=reservation.count,
    )
    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation)

    # プロジェクト取得
    project = await db.scalar(select(TheaterProject).where(TheaterProject.id == milestone.project_id))

    # メール送信 (Background)
    # DBはNaive UTCで保存されているため、JSTに変換して表示
    jst = timezone(timedelta(hours=9))
    start_date_utc = milestone.start_date.replace(tzinfo=timezone.utc)
    start_date_jst = start_date_utc.astimezone(jst)
    date_str = start_date_jst.strftime("%Y/%m/%d %H:%M")
    
    background_tasks.add_task(
        email_service.send_reservation_confirmation,
        to_email=reservation.email,
        name=reservation.name,
        milestone_title=milestone.title,
        date_str=date_str,
        count=reservation.count,
        project_name=project.name if project else "不明なプロジェクト"
    )

    return db_reservation


@router.get("/public/milestones/{id}", response_model=MilestoneResponse)
async def get_public_milestone(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """公開マイルストーン詳細取得."""
    milestone = await db.scalar(
        select(Milestone)
        .options(selectinload(Milestone.project))
        .where(Milestone.id == id)
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # Pydanticモデルのために辞書化して project_name を追加
    response = MilestoneResponse.model_validate(milestone)
    if milestone.project:
        response.project_name = milestone.project.name
        
    return response


@router.get("/public/projects/{project_id}/members")
async def get_project_members_public(
    project_id: str,
    role: str | None = Query(None, description="Filter by role (e.g. 'cast')"),
    db: AsyncSession = Depends(get_db),
):
    """紹介者リスト取得 (Public)."""
    stmt = select(User, ProjectMember).join(ProjectMember, User.id == ProjectMember.user_id).where(ProjectMember.project_id == project_id)

    if role == "cast":
        # キャストとして配役されているユーザーのみ
        stmt = stmt.join(CharacterCasting, CharacterCasting.user_id == User.id)

    # 重複排除のためにdistinctを使用する場合、組み合わせに注意が必要だが、
    # 1ユーザー1メンバーレコードなので基本User単位でユニークになるはず。
    # ただしCharacterCastingで複数役の場合重複する可能性があるためdistinctする。
    result = await db.execute(stmt.distinct())
    rows = result.all()
    
    response = []
    seen_ids = set()
    for user, member in rows:
        if user.id in seen_ids:
            continue
        seen_ids.add(user.id)
        
        name = member.display_name or user.screen_name or user.discord_username
        response.append({"id": user.id, "name": name})

    return response


# --- Internal API ---

@router.get("/projects/{project_id}/reservations", response_model=list[ReservationResponse])
async def get_reservations(
    project_id: str,
    milestone_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予約一覧取得."""
    # 権限チェック: プロジェクトメンバーであること
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    stmt = select(Reservation).join(Milestone).where(Milestone.project_id == project_id)
    if milestone_id:
        stmt = stmt.where(Reservation.milestone_id == milestone_id)
    
    stmt = stmt.options(
        selectinload(Reservation.milestone),
        selectinload(Reservation.referral_user)
    ).order_by(Reservation.created_at.desc())
    
    result = await db.scalars(stmt)
    reservations = result.all()

    # Response整形
    # 紹介者の情報を取得するために、Reservation -> ReferralUser -> ProjectMember(そのプロジェクトの) を取得したいが、
    # Eager Loadingでそこまで絞り込むのは複雑なため、単純にReservation取得後に都度解決するか、
    # あるいは ProjectMember も join して fetch する。
    # ここではループ内で取得するコストを避けるため、プロジェクトメンバー辞書を作成しておく。
    
    # 全プロジェクトメンバー取得
    pm_stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    pm_result = await db.scalars(pm_stmt)
    pm_map = {pm.user_id: pm for pm in pm_result.all()}

    # Response整形
    results = []
    for r in reservations:
        res_dict = r.__dict__.copy()
        res_dict["milestone_title"] = r.milestone.title
        
        referral_name = None
        if r.referral_user:
            # プロジェクトメンバーとしての情報を優先
            pm = pm_map.get(r.referral_user_id)
            if pm and pm.display_name:
                referral_name = pm.display_name
            else:
                referral_name = r.referral_user.screen_name or r.referral_user.discord_username
        
        res_dict["referral_name"] = referral_name
        results.append(res_dict)
        
    return results


@router.patch("/reservations/{reservation_id}/attendance", response_model=ReservationResponse)
async def update_attendance(
    reservation_id: str,
    update_data: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """出欠更新."""
    reservation = await db.scalar(
        select(Reservation).options(selectinload(Reservation.milestone)).where(Reservation.id == reservation_id)
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 権限チェック
    project_id = reservation.milestone.project_id
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    reservation.attended = update_data.attended
    await db.commit()
    await db.refresh(reservation)

    res_dict = reservation.__dict__.copy()
    res_dict["milestone_title"] = reservation.milestone.title
    return res_dict


@router.post("/projects/{project_id}/reservations/export")
async def export_reservations(
    project_id: str,
    milestone_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSVエクスポート."""
        # 権限チェック: プロジェクトメンバーであること
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    stmt = select(Reservation).join(Milestone).where(Milestone.project_id == project_id)
    if milestone_id:
        stmt = stmt.where(Reservation.milestone_id == milestone_id)
        
    stmt = stmt.options(
        selectinload(Reservation.milestone),
        selectinload(Reservation.referral_user)
    ).order_by(Reservation.milestone_id, Reservation.created_at)
    
    result = await db.scalars(stmt)
    reservations = result.all()

    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "公演名", "日時", "予約者名", "Email", "人数", 
        "紹介者", "出席", "予約日時"
    ])
    
    # 全プロジェクトメンバー取得（名前解決用）
    pm_stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    pm_result = await db.scalars(pm_stmt)
    pm_map = {pm.user_id: pm for pm in pm_result.all()}

    for r in reservations:
        referral = ""
        if r.referral_user:
            pm = pm_map.get(r.referral_user_id)
            if pm and pm.display_name:
                referral = pm.display_name
            else:
                referral = r.referral_user.screen_name or r.referral_user.discord_username

        date_str = r.milestone.start_date.strftime("%Y/%m/%d %H:%M")
        created_str = r.created_at.strftime("%Y/%m/%d %H:%M:%S")
        writer.writerow([
            str(r.id), r.milestone.title, date_str, r.name, r.email, r.count,
            referral, "済" if r.attended else "未", created_str
        ])
    
    output.seek(0)
    
    # ファイル名用の日時
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reservations_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
