from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import (
    User, TheaterProject, ProjectMember, Milestone, Reservation,
    Character, CharacterCasting, Script
)
from src.services.email import email_service


@pytest.fixture
async def project(db: AsyncSession) -> TheaterProject:
    project = TheaterProject(name="Test Project", is_public=True)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@pytest.fixture
async def milestone(db: AsyncSession, project: TheaterProject) -> Milestone:
    ms = Milestone(
        project_id=project.id,
        title="Test Milestone",
        start_date=datetime.now() + timedelta(days=7),
        reservation_capacity=10  # 定員10名
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms

@pytest.fixture
async def project_member(db: AsyncSession, project: TheaterProject) -> User:
    user = User(discord_id="12345", discord_username="member", discord_avatar_hash="hash")
    db.add(user)
    await db.flush()
    pm = ProjectMember(project_id=project.id, user_id=user.id, role="viewer")
    db.add(pm)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.fixture
async def cast_member(db: AsyncSession, project: TheaterProject) -> User:
    user_id = uuid4()
    user = User(id=user_id, discord_id="67890", discord_username="cast", screen_name="Actor A")
    db.add(user)
    await db.flush()
    
    script_id = uuid4()
    script = Script(id=script_id, project_id=project.id, uploaded_by=user_id, title="Test Script", content="")
    db.add(script)
    await db.flush()
    
    char = Character(script_id=script_id, name="Hero")
    db.add(char)
    await db.flush()
    
    casting = CharacterCasting(character_id=char.id, user_id=user_id)
    db.add(casting)
    pm = ProjectMember(project_id=project.id, user_id=user_id, role="viewer")
    db.add(pm)
    await db.commit()
    await db.refresh(user)
    return user
    
    casting = CharacterCasting(character_id=char.id, user_id=user.id)
    db.add(casting)
    pm = ProjectMember(project_id=project.id, user_id=user.id, role="viewer")
    db.add(pm)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_reservation_success(client: AsyncClient, milestone: Milestone):
    """予約作成成功時テスト."""
    payload = {
        "milestone_id": str(milestone.id),
        "name": "Guest User",
        "email": "guest@example.com",
        "count": 2
    }
    
    # SendGridのモック
    with patch.object(email_service, "send_reservation_confirmation") as mock_send:
        response = await client.post("/api/public/reservations", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Guest User"
    assert data["count"] == 2
    
    # BackgroundTasksの実行を確認
    mock_send.assert_called()
    call_args = mock_send.call_args
    assert call_args is not None
    _, kwargs = call_args
    assert kwargs["to_email"] == "guest@example.com"
    assert kwargs["name"] == "Guest User"
    assert kwargs["project_name"] == "Test Project"


@pytest.mark.asyncio
async def test_create_reservation_capacity_error(client: AsyncClient, db: AsyncSession, milestone: Milestone):
    """定員オーバーエラーテスト."""
    # 既に9名予約済み (定員10名)
    r1 = Reservation(
        milestone_id=milestone.id, name="Existing", email="e@e.com", count=9
    )
    db.add(r1)
    await db.commit()
    
    # 2名予約しようとするとオーバー (9+2 > 10)
    payload = {
        "milestone_id": str(milestone.id),
        "name": "Late User",
        "email": "late@example.com",
        "count": 2
    }
    response = await client.post("/api/public/reservations", json=payload)
    assert response.status_code == 400
    assert "capacity exceeded" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_cast_members_public(client: AsyncClient, db: AsyncSession, project: TheaterProject, cast_member: User, project_member: User):
    """紹介者リスト(キャスト絞り込み)テスト."""
    # キャストのみ
    response = await client.get(f"/api/public/projects/{project.id}/members?role=cast")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Actor A" # screen_name優先, ProjectMember.display_name設定なし
    
    # ProjectMemberのdisplay_nameを設定
    stmt = select(ProjectMember).where(ProjectMember.user_id == cast_member.id)
    result = await db.execute(stmt)
    cast_member_pm = result.scalar_one()
    cast_member_pm.display_name = "Stage Name A"
    await db.commit()
    
    response = await client.get(f"/api/public/projects/{project.id}/members?role=cast")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == "Stage Name A" # display_name優先

    # 全員
    response = await client.get(f"/api/public/projects/{project.id}/members")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_admin_reservation_list(client: AsyncClient, db: AsyncSession, project: TheaterProject, milestone: Milestone, project_member: User):
    """管理者予約一覧取得テスト."""
    # 予約作成
    r = Reservation(milestone_id=milestone.id, name="R1", email="r1@e.com", count=1)
    db.add(r)
    await db.commit()
    
    from src.dependencies.auth import get_current_user_dep
    # Get the FastAPI app from the client (since it's an ASGITransport wrapped client)
    from src.main import app
    app.dependency_overrides[get_current_user_dep] = lambda: project_member

    try:
        response = await client.get(f"/api/projects/{project.id}/reservations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "R1"
    finally:
        app.dependency_overrides.pop(get_current_user_dep, None)

@pytest.mark.asyncio
async def test_update_attendance(client: AsyncClient, db: AsyncSession, milestone: Milestone, project_member: User):
    """出欠更新テスト."""
    r = Reservation(milestone_id=milestone.id, name="R2", email="r2@e.com", count=1, attended=False)
    db.add(r)
    await db.commit()
    
    from src.dependencies.auth import get_current_user_dep
    from src.main import app
    app.dependency_overrides[get_current_user_dep] = lambda: project_member

    try:
        response = await client.patch(f"/api/reservations/{r.id}/attendance", json={"attended": True})
        assert response.status_code == 200
        assert response.json()["attended"] is True
    finally:
        app.dependency_overrides.pop(get_current_user_dep, None)

@pytest.mark.asyncio
async def test_export_csv(client: AsyncClient, db: AsyncSession, project: TheaterProject, milestone: Milestone, project_member: User):
    """CSVエクスポートテスト."""
    r = Reservation(milestone_id=milestone.id, name="CSV User", email="csv@e.com", count=3)
    db.add(r)
    await db.commit()
    
    from src.dependencies.auth import get_current_user_dep
    from src.main import app
    app.dependency_overrides[get_current_user_dep] = lambda: project_member

    try:
        response = await client.post(f"/api/projects/{project.id}/reservations/export")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "CSV User" in response.text
    finally:
        app.dependency_overrides.pop(get_current_user_dep, None)


@pytest.mark.asyncio
async def test_cancel_reservation(client: AsyncClient, db: AsyncSession, milestone: Milestone):
    """予約キャンセルテスト."""
    r = Reservation(milestone_id=milestone.id, name="Cancel User", email="cancel@e.com", count=1)
    db.add(r)
    await db.commit()
    r_id = str(r.id)
    
    # Discord通知を飛ばすためにWebhook URLを設定
    project = await db.get(TheaterProject, milestone.project_id)
    project.discord_webhook_url = "http://fake-webhook"
    await db.commit()
    
    # 成功
    payload = {"reservation_id": r_id, "email": "cancel@e.com"}
    
    # Discordのモック
    with patch("src.services.discord.DiscordService.send_notification") as mock_discord:
        response = await client.post("/api/public/reservations/cancel", json=payload)
    
    assert response.status_code == 204
    # DBから消えているか
    assert await db.get(Reservation, r.id) is None
    mock_discord.assert_called() # 呼ばれていること

    # 失敗（存在しない）
    response = await client.post("/api/public/reservations/cancel", json=payload)
    assert response.status_code == 404
    
    # 失敗（メール不一致）
    # 再作成
    r2 = Reservation(milestone_id=milestone.id, name="User2", email="u2@e.com", count=1)
    db.add(r2)
    await db.commit()
    
    payload_mismatch = {"reservation_id": str(r2.id), "email": "wrong@e.com"}
    response = await client.post("/api/public/reservations/cancel", json=payload_mismatch)
    assert response.status_code == 404
    
    
@pytest.mark.asyncio
async def test_public_schedule(client: AsyncClient, db: AsyncSession, project: TheaterProject, milestone: Milestone):
    """公開スケジュール取得テスト."""
    milestone.start_date = datetime.now() + timedelta(days=1) # 未来
    await db.commit()
    
    response = await client.get("/api/public/schedule")
    assert response.status_code == 200
    data = response.json()
    
    # 含まれているか
    found = any(m["id"] == str(milestone.id) for m in data)
    assert found
    
    # プロジェクト名が含まれているか
    target = next(m for m in data if m["id"] == str(milestone.id))
    assert target["project_name"] == project.name

