"""マイルストーン別予約取得エンドポイントを追加するパッチファイル."""
# このコードをreservations.pyの364行目の前に挿入してください

milestone_reservations_endpoint = '''
@router.get("/milestones/{milestone_id}/reservations", response_model=list[ReservationResponse])
async def get_milestone_reservations(
    milestone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """特定マイルストーンの予約一覧を取得."""
    # マイルストーン取得
    milestone = await db.scalar(
        select(Milestone).where(Milestone.id == milestone_id)
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    # 権限チェック
    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == milestone.project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    
    # 予約取得
    stmt = (
        select(Reservation)
        .where(Reservation.milestone_id == milestone_id)
        .order_by(Reservation.created_at.desc())
    )
    result = await db.execute(stmt)
    reservations = result.scalars().all()
    
    # レスポンス作成
    response_list = []
    for reservation in reservations:
        # 紹介者名の取得
        referral_name = None
        if reservation.referral_user_id:
            ref_user = await db.scalar(select(User).where(User.id == reservation.referral_user_id))
            if ref_user:
                ref_pm = await db.scalar(
                    select(ProjectMember).where(
                        ProjectMember.user_id == reservation.referral_user_id,
                        ProjectMember.project_id == milestone.project_id
                    )
                )
                referral_name = (
                    (ref_pm.display_name if ref_pm and ref_pm.display_name else None)
                    or ref_user.screen_name
                    or ref_user.discord_username
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
                referral_name=referral_name
            )
        )
    
    return response_list


'''
print(milestone_reservations_endpoint)
