import csv
import io
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from src.db.base import get_db
from src.db.models import Reservation, User, Milestone, TheaterProject, ProjectMember, CharacterCasting
from src.schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from src.services.email import email_service
from src.dependencies.auth import get_current_user_dep as get_current_user, get_optional_current_user_dep as get_current_user_optional

router = APIRouter()

# --- Public API ---

@router.post("/public/reservations", response_model=ReservationResponse)
def create_reservation(
    reservation: ReservationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """予約作成 (Public)."""
    # マイルストーン取得
    milestone = db.scalar(select(Milestone).where(Milestone.id == reservation.milestone_id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # 定員チェック
    if milestone.reservation_capacity is not None:
        current_count = db.scalar(
            select(func.sum(Reservation.count))
            .where(Reservation.milestone_id == reservation.milestone_id)
        ) or 0
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
    db.commit()
    db.refresh(db_reservation)

    # メール送信 (Background)
    date_str = milestone.start_date.strftime("%Y/%m/%d %H:%M")
    background_tasks.add_task(
        email_service.send_reservation_confirmation,
        to_email=reservation.email,
        name=reservation.name,
        milestone_title=milestone.title,
        date_str=date_str,
        count=reservation.count
    )

    return db_reservation


from src.schemas.project import MilestoneResponse

@router.get("/public/milestones/{id}", response_model=MilestoneResponse)
def get_public_milestone(
    id: str,
    db: Session = Depends(get_db),
):
    """公開マイルストーン詳細取得."""
    milestone = db.scalar(select(Milestone).where(Milestone.id == id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # MilestoneResponseではproject_idが含まれていたりと、必要情報は網羅されている
    # 必要ならProjectがis_publicかもチェックすべきだが、
    # 予約リンクを知っている＝アクセス可能、とするか、
    # あるいは Project.is_public == True もチェックするか。
    # 以前のRequirementsでは「公演のマイルストーンに対して」とあるので、
    # 公開プロジェクトのマイルストーン、あるいは予約用URLを知っている前提。
    # 念のためProjectの存在確認とPublicチェックを入れるのが安全だが、
    # 一旦チケット予約はURL共有ベースで動くことも多いため、Milestoneが存在すればOKとする。
    
    return milestone


@router.get("/public/projects/{project_id}/members")
def get_project_members_public(
    project_id: str,
    role: str | None = Query(None, description="Filter by role (e.g. 'cast')"),
    db: Session = Depends(get_db),
):
    """紹介者リスト取得 (Public)."""
    stmt = select(User).join(ProjectMember).where(ProjectMember.project_id == project_id)

    if role == "cast":
        # キャストとして配役されているユーザーのみ
        stmt = stmt.join(CharacterCasting, CharacterCasting.user_id == User.id)

    users = db.scalars(stmt.distinct()).all()
    
    return [
        {"id": user.id, "name": user.screen_name or user.discord_username}
        for user in users
    ]


# --- Internal API ---

@router.get("/projects/{project_id}/reservations", response_model=list[ReservationResponse])
def get_reservations(
    project_id: str,
    milestone_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予約一覧取得."""
    # 権限チェック: プロジェクトメンバーであること
    member = db.scalar(
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
    
    reservations = db.scalars(stmt).all()

    # Response整形
    results = []
    for r in reservations:
        res_dict = r.__dict__.copy()
        res_dict["milestone_title"] = r.milestone.title
        res_dict["referral_name"] = (
            r.referral_user.screen_name or r.referral_user.discord_username
        ) if r.referral_user else None
        results.append(res_dict)
        
    return results


@router.patch("/reservations/{reservation_id}/attendance", response_model=ReservationResponse)
def update_attendance(
    reservation_id: str,
    update_data: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """出欠更新."""
    reservation = db.scalar(
        select(Reservation).options(selectinload(Reservation.milestone)).where(Reservation.id == reservation_id)
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 権限チェック
    project_id = reservation.milestone.project_id
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    reservation.attended = update_data.attended
    db.commit()
    db.refresh(reservation)

    res_dict = reservation.__dict__.copy()
    res_dict["milestone_title"] = reservation.milestone.title
    return res_dict


@router.post("/projects/{project_id}/reservations/export")
def export_reservations(
    project_id: str,
    milestone_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSVエクスポート."""
        # 権限チェック: プロジェクトメンバーであること
    member = db.scalar(
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
    
    reservations = db.scalars(stmt).all()

    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "公演名", "日時", "予約者名", "Email", "人数", 
        "紹介者", "出席", "予約日時"
    ])
    
    for r in reservations:
        referral = (r.referral_user.screen_name or r.referral_user.discord_username) if r.referral_user else ""
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
