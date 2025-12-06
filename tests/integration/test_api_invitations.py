import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import ProjectInvitation, TheaterProject, User, ProjectMember
from src.auth.jwt import create_access_token

@pytest.mark.asyncio
async def test_create_invitation(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    test_project: TheaterProject
) -> None:
    """招待作成テスト."""
    # test_projectフィクスチャですでにtest_userはownerとして追加されているため、
    # ここでのメンバー追加は不要（むしろ重複エラーになる）
    
    token = create_access_token({"sub": str(test_user.id)})
    
    response = await client.post(
        f"/projects/{test_project.id}/invitations",
        json={"expires_in_hours": 24, "max_uses": 5},
        params={"token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == test_project.id
    assert data["max_uses"] == 5
    assert "token" in data

@pytest.mark.asyncio
async def test_get_invitation(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    test_project: TheaterProject
) -> None:
    """招待取得テスト."""
    # 招待作成
    from datetime import datetime, timedelta, timezone
    inv_token = "test_token_123"
    inv = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token=inv_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        max_uses=10,
        used_count=0
    )
    db.add(inv)
    await db.commit()
    
    response = await client.get(f"/invitations/{inv_token}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == inv_token
    assert data["project_name"] == test_project.name

@pytest.mark.asyncio
async def test_accept_invitation(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User  # owner
) -> None:
    """招待受諾テスト."""
    # 別のユーザーを作成（招待される人）
    new_user = User(
        discord_id="99999",
        discord_username="new_member",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # 招待作成
    from datetime import datetime, timedelta, timezone
    inv_token = "test_token_accept"
    inv = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token=inv_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        max_uses=1,
        used_count=0
    )
    db.add(inv)
    await db.commit()
    
    # 実行
    token = create_access_token({"sub": str(new_user.id)})
    response = await client.post(
        f"/invitations/{inv_token}/accept",
        params={"token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "プロジェクトに参加しました"
    
    # 再度実行（上限切れを確認したいが、まずは冪等性またはエラー）
    # 今回の実装ではused_countを見てるが、トランザクション分離レベルによっては同時実行注意
    # ここでは単純にメンバーになってるか確認
    
    # used_countが増えているか
    await db.refresh(inv)
    assert inv.used_count == 1
