import csv
import io
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import get_db
from src.db.models import (
    CharacterCasting,
    Milestone,
    ProjectMember,
    Reservation,
    TheaterProject,
    User,
)
from src.dependencies.auth import get_current_user_dep as get_current_user
from src.dependencies.auth import get_optional_current_user_dep as get_current_user_optional
from src.schemas.project import MilestoneResponse
from src.schemas.reservation import (
    ReservationCancel,
    ReservationCreate,
    ReservationResponse,
    ReservationUpdate,
)
from src.services.email import email_service

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
            select(func.sum(Reservation.count)).where(
                Reservation.milestone_id == reservation.milestone_id
            )
        )
        current_count = result or 0
        remaining = milestone.reservation_capacity - current_count
        if current_count + reservation.count > milestone.reservation_capacity:
            raise HTTPException(
                status_code=400, detail=f"Capacity exceeded. Only {remaining} tickets remaining."
            )

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
    project = await db.scalar(
        select(TheaterProject).where(TheaterProject.id == milestone.project_id)
    )

    # Discord Timestamp for notifications
    milestone_ts = int(milestone.start_date.replace(tzinfo=UTC).timestamp())
    discord_date_str = f"<t:{milestone_ts}:f>"

    # Mail still needs formatted string (keep JST as default for mail)
    jst = timezone(timedelta(hours=9))
    start_date_utc = milestone.start_date.replace(tzinfo=UTC)
    start_date_jst = start_date_utc.astimezone(jst)
    date_str = start_date_jst.strftime("%Y/%m/%d %H:%M")

    background_tasks.add_task(
        email_service.send_reservation_confirmation,
        to_email=reservation.email,
        name=reservation.name,
        milestone_title=milestone.title,
        date_str=date_str,
        count=reservation.count,
        project_name=project.name if project else "不明なプロジェクト",
        reservation_id=str(db_reservation.id),
        location=milestone.location,  # 🆕 場所を追加
        description=milestone.description,  # 🆕 説明を追加
    )

    # Discord通知 (Webhook)
    # プロジェクトに設定されたWebhookを使用
    if project and project.discord_webhook_url:
        from src.services.discord import get_discord_service

        discord_service = get_discord_service()

        # 扱い（紹介者）の取得
        referral_name = "なし"
        if reservation.referral_user_id:
            # ここでは簡易的にUserテーブル等から取得（あるいはProjectMember）
            # get_project_members_public のロジックと同様に解決するのが理想だが、
            # バックグラウンドタスク内でそこまで重い処理をしたくないため、
            # 一旦ID解決せず、もしあればキャッシュ等... ないので、
            # クエリ発行して名前取得
            try:
                ref_user = await db.scalar(
                    select(User).where(User.id == reservation.referral_user_id)
                )
                if ref_user:
                    # ProjectMemberも見てdisplay_nameがあればそれを使う
                    ref_pm = await db.scalar(
                        select(ProjectMember).where(
                            ProjectMember.user_id == reservation.referral_user_id,
                            ProjectMember.project_id == project.id,
                        )
                    )
                    referral_name = (
                        (ref_pm.display_name if ref_pm and ref_pm.display_name else None)
                        or ref_user.display_name
                        or "不明"
                    )
            except Exception:
                # 失敗しても通知は送る
                pass

        notification_content = f"""🎫 **チケット予約完了**
公演日時: {discord_date_str}
お名前: {reservation.name}
予約枚数: {reservation.count}枚
扱い: {referral_name}
"""
        background_tasks.add_task(
            discord_service.send_notification,
            content=notification_content,
            webhook_url=project.discord_webhook_url,
        )

    return db_reservation


@router.get("/public/milestones/{id}", response_model=MilestoneResponse)
async def get_public_milestone(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    """公開マイルストーン詳細取得."""
    # UUID形式のバリデーション
    try:
        from uuid import UUID

        UUID(id)  # UUIDとして解析できるか確認
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid milestone ID format. Must be a valid UUID."
        )

    # マイルストーンと予約数を同時に取得
    from sqlalchemy import func
    # ✅ Reservationは既にファイル先頭でインポート済み

    stmt = (
        select(Milestone, func.coalesce(func.sum(Reservation.count), 0).label("total_reserved"))
        .outerjoin(Reservation, Milestone.id == Reservation.milestone_id)
        .join(TheaterProject, Milestone.project_id == TheaterProject.id)
        .options(selectinload(Milestone.project))
        .where(
            Milestone.id == id,
            Milestone.is_public == True,  # マイルストーンのis_publicのみチェック
        )
        .group_by(Milestone.id)
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Milestone not found")

    milestone, total_reserved = row

    # Pydanticモデルのために辞書化して project_name と current_reservation_count を追加
    response = MilestoneResponse.model_validate(milestone)
    response.current_reservation_count = total_reserved
    if milestone.project:
        response.project_name = milestone.project.name

    return response


@router.get("/public/projects/{project_id}/members")
async def get_project_members_public(
    project_id: UUID,
    role: str | None = Query(None, description="Filter by role (e.g. 'cast')"),
    db: AsyncSession = Depends(get_db),
):
    """紹介者リスト取得 (Public)."""
    stmt = (
        select(User, ProjectMember)
        .join(ProjectMember, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )

    if role == "cast":
        # キャストとして配役されているユーザーのみ
        # 注意: CharacterCasting -> Character -> Script と辿って project_id を確認する
        from src.db.models import Character, Script

        stmt = (
            stmt.join(CharacterCasting, CharacterCasting.user_id == User.id)
            .join(Character, Character.id == CharacterCasting.character_id)
            .join(Script, Script.id == Character.script_id)
            .where(Script.project_id == project_id)
        )

    # 重複排除のためにdistinctを使用
    result = await db.execute(stmt.distinct())
    rows = result.all()

    response = []
    seen_ids = set()
    for user, member in rows:
        if user.id in seen_ids:
            continue
        seen_ids.add(user.id)

        name = member.display_name or user.display_name
        response.append({"id": user.id, "name": name})

    return response


@router.post("/public/reservations/cancel", status_code=204)
async def cancel_reservation(
    cancel_data: ReservationCancel,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """予約キャンセル (Public)."""
    reservation = await db.scalar(
        select(Reservation)
        .options(selectinload(Reservation.milestone))
        .where(Reservation.id == cancel_data.reservation_id, Reservation.email == cancel_data.email)
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found or email mismatch")

    # データ保持用
    milestone_title = reservation.milestone.title
    start_date = reservation.milestone.start_date
    project_id = reservation.milestone.project_id
    res_name = reservation.name
    res_count = reservation.count
    res_ref_id = reservation.referral_user_id

    # 削除
    await db.delete(reservation)
    await db.commit()

    # 通知 (Discord)
    project = await db.scalar(select(TheaterProject).where(TheaterProject.id == project_id))
    if project and project.discord_webhook_url:
        from src.services.discord import get_discord_service

        discord_service = get_discord_service()

        # 扱い（紹介者）の取得
        referral_name = "なし"
        if res_ref_id:
            try:
                ref_user = await db.scalar(select(User).where(User.id == res_ref_id))
                if ref_user:
                    ref_pm = await db.scalar(
                        select(ProjectMember).where(
                            ProjectMember.user_id == res_ref_id,
                            ProjectMember.project_id == project.id,
                        )
                    )
                    referral_name = (
                        (ref_pm.display_name if ref_pm and ref_pm.display_name else None)
                        or ref_user.display_name
                        or "不明"
                    )
            except:
                pass

        # Discord Timestamp for notifications
        milestone_ts = int(start_date.replace(tzinfo=UTC).timestamp())
        discord_date_str = f"<t:{milestone_ts}:f>"

        # 日時JST変換
        jst = timezone(timedelta(hours=9))
        start_date_utc = start_date.replace(tzinfo=UTC)
        date_str = start_date_utc.astimezone(jst).strftime("%Y/%m/%d %H:%M")

        notification_content = f"""🗑️ **チケット予約キャンセル**
公演日時: {discord_date_str}
お名前: {res_name}
予約枚数: {res_count}枚
扱い: {referral_name}
"""
        background_tasks.add_task(
            discord_service.send_notification,
            content=notification_content,
            webhook_url=project.discord_webhook_url,
        )


@router.get("/public/schedule", response_model=list[MilestoneResponse])
async def get_public_schedule(
    db: AsyncSession = Depends(get_db),
):
    """公開スケジュール取得."""
    # 公開プロジェクトの未来のマイルストーンを取得
    now = datetime.now(UTC)

    # プロジェクトがpublicで、マイルストーンが未来のもの
    stmt = (
        select(Milestone)
        .join(TheaterProject, Milestone.project_id == TheaterProject.id)
        .options(selectinload(Milestone.project))
        .where(
            Milestone.is_public == True,  # マイルストーンのis_publicのみチェック
            Milestone.start_date >= now,
        )
        .order_by(Milestone.start_date)
    )
    result = await db.scalars(stmt)
    milestones = result.all()

    response = []
    for m in milestones:
        m_res = MilestoneResponse.model_validate(m)
        if m.project:
            m_res.project_name = m.project.name
        response.append(m_res)

    return response


# --- Internal API ---


@router.get("/projects/{project_id}/reservations", response_model=list[ReservationResponse])
async def get_reservations(
    project_id: UUID,
    milestone_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予約一覧取得."""
    # 権限チェック: プロジェクトメンバーであること
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    stmt = select(Reservation).join(Milestone).where(Milestone.project_id == project_id)
    if milestone_id:
        stmt = stmt.where(Reservation.milestone_id == milestone_id)

    stmt = stmt.options(
        selectinload(Reservation.milestone), selectinload(Reservation.referral_user)
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
                referral_name = r.referral_user.display_name

        res_dict["referral_name"] = referral_name
        results.append(res_dict)

    return results


@router.get("/milestones/{milestone_id}/reservations", response_model=list[ReservationResponse])
async def get_milestone_reservations(
    milestone_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """特定マイルストーンの予約一覧を取得."""
    milestone = await db.scalar(select(Milestone).where(Milestone.id == milestone_id))
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == milestone.project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    stmt = (
        select(Reservation)
        .where(Reservation.milestone_id == milestone_id)
        .order_by(Reservation.created_at.desc())
    )
    result = await db.execute(stmt)
    reservations = result.scalars().all()

    response_list = []
    for reservation in reservations:
        referral_name = None
        if reservation.referral_user_id:
            ref_user = await db.scalar(select(User).where(User.id == reservation.referral_user_id))
            if ref_user:
                ref_pm = await db.scalar(
                    select(ProjectMember).where(
                        ProjectMember.user_id == reservation.referral_user_id,
                        ProjectMember.project_id == milestone.project_id,
                    )
                )
                referral_name = (
                    (ref_pm.display_name if ref_pm and ref_pm.display_name else None)
                    or ref_user.display_name
                    or "不明"
                )

        response_list.append(
            ReservationResponse(
                id=str(reservation.id),
                milestone_id=str(reservation.milestone_id),
                milestone_title=milestone.title,
                name=reservation.name,
                email=reservation.email,
                count=reservation.count,
                attended=reservation.attended,
                created_at=reservation.created_at,
                referral_name=referral_name,
            )
        )

    return response_list


@router.patch("/reservations/{reservation_id}/attendance", response_model=ReservationResponse)
async def update_attendance(
    reservation_id: UUID,
    update_data: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """出欠更新."""
    reservation = await db.scalar(
        select(Reservation)
        .options(selectinload(Reservation.milestone))
        .where(Reservation.id == reservation_id)
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # 権限チェック
    project_id = reservation.milestone.project_id
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
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
    project_id: UUID,
    milestone_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSVエクスポート."""
    # 権限チェック: プロジェクトメンバーであること
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    stmt = select(Reservation).join(Milestone).where(Milestone.project_id == project_id)
    if milestone_id:
        stmt = stmt.where(Reservation.milestone_id == milestone_id)

    stmt = stmt.options(
        selectinload(Reservation.milestone), selectinload(Reservation.referral_user)
    ).order_by(Reservation.milestone_id, Reservation.created_at)

    result = await db.scalars(stmt)
    reservations = result.all()

    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)

    # Viewer権限の場合、メールアドレスを非表示
    is_viewer = member.role == "viewer"

    if is_viewer:
        writer.writerow(["ID", "公演名", "日時", "予約者名", "人数", "紹介者", "出席", "予約日時"])
    else:
        writer.writerow(
            ["ID", "公演名", "日時", "予約者名", "Email", "人数", "紹介者", "出席", "予約日時"]
        )

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
                referral = r.referral_user.display_name

        date_str = r.milestone.start_date.strftime("%Y/%m/%d %H:%M")
        created_str = r.created_at.strftime("%Y/%m/%d %H:%M:%S")

        if is_viewer:
            writer.writerow(
                [
                    str(r.id),
                    r.milestone.title,
                    date_str,
                    r.name,
                    r.count,
                    referral,
                    "済" if r.attended else "未",
                    created_str,
                ]
            )
        else:
            writer.writerow(
                [
                    str(r.id),
                    r.milestone.title,
                    date_str,
                    r.name,
                    r.email,
                    r.count,
                    referral,
                    "済" if r.attended else "未",
                    created_str,
                ]
            )

    output.seek(0)

    # ファイル名用の日時
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reservations_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/admin/tasks/send-event-reminders")
async def send_event_reminders_manually(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """リマインダーメール手動送信（管理者用）."""
    # 任意のプロジェクトのownerまたはeditorであることを確認
    # 簡易的にプロジェクトメンバーであればOKとする
    member = await db.scalar(select(ProjectMember).where(ProjectMember.user_id == current_user.id))
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    # タスク実行
    from src.services.reservation_tasks import check_todays_events

    stats = await check_todays_events()

    return {"message": "Event reminder task completed", "stats": stats}
