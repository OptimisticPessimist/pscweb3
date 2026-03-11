from datetime import UTC

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import create_access_token
from src.db.models import ProjectInvitation, TheaterProject, User


@pytest.mark.asyncio
async def test_create_invitation(
    client: AsyncClient, db: AsyncSession, test_user: User, test_project: TheaterProject
) -> None:
    """招待作成テスト."""
    # test_projectフィクスチャですでにtest_userはownerとして追加されているため、
    # ここでのメンバー追加は不要（むしろ重複エラーになる）

    token = create_access_token({"sub": str(test_user.id)})

    response = await client.post(
        f"/api/projects/{test_project.id}/invitations",
        json={"expires_in_hours": 24, "max_uses": 5},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    assert data["max_uses"] == 5
    assert "token" in data


@pytest.mark.asyncio
async def test_get_invitation(
    client: AsyncClient, db: AsyncSession, test_user: User, test_project: TheaterProject
) -> None:
    """招待取得テスト."""
    # 招待作成
    from datetime import datetime, timedelta

    inv_token = "test_token_123"
    inv = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token=inv_token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        max_uses=10,
        used_count=0,
    )
    db.add(inv)
    await db.commit()

    response = await client.get(f"/api/invitations/{inv_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == inv_token
    assert data["project_name"] == test_project.name


@pytest.mark.asyncio
async def test_accept_invitation(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,  # owner
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
    from datetime import datetime, timedelta

    inv_token = "test_token_accept"
    inv = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token=inv_token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        max_uses=1,
        used_count=0,
    )
    db.add(inv)
    await db.commit()

    # 実行
    token = create_access_token({"sub": str(new_user.id)})
    response = await client.post(
        f"/api/invitations/{inv_token}/accept", headers={"Authorization": f"Bearer {token}"}
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


@pytest.mark.asyncio
async def test_list_project_invitations(
    client: AsyncClient, db: AsyncSession, test_user: User, test_project: TheaterProject
) -> None:
    """招待一覧取得テスト."""
    from datetime import datetime, timedelta

    now = datetime.now(UTC)

    # 1. 有効な招待
    inv1 = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="valid_token",
        expires_at=now + timedelta(hours=24),
        max_uses=None,
        used_count=0,
    )
    # 2. 期限切れ
    inv2 = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="expired_token",
        expires_at=now - timedelta(hours=1),
        max_uses=None,
        used_count=0,
    )
    # 3. 使用回数上限
    inv3 = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="max_uses_token",
        expires_at=now + timedelta(hours=24),
        max_uses=1,
        used_count=1,
    )

    db.add_all([inv1, inv2, inv3])
    await db.commit()

    token = create_access_token({"sub": str(test_user.id)})
    response = await client.get(
        f"/api/projects/{test_project.id}/invitations", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["token"] == "valid_token"


@pytest.mark.asyncio
async def test_delete_invitation(
    client: AsyncClient, db: AsyncSession, test_user: User, test_project: TheaterProject
) -> None:
    """招待削除テスト."""
    from datetime import datetime, timedelta

    inv_token = "token_to_delete"
    inv = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token=inv_token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        max_uses=None,
        used_count=0,
    )
    db.add(inv)
    await db.commit()

    token = create_access_token({"sub": str(test_user.id)})

    # 削除実行
    response = await client.delete(
        f"/api/invitations/{inv_token}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # 削除されているか確認
    query = select(ProjectInvitation).where(ProjectInvitation.token == inv_token)
    result = await db.execute(query)
    assert result.scalar_one_or_none() is None

    # 権限なしテスト
    # 別ユーザー作成
    other_user = User(discord_id="other", discord_username="other")
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    # 新しい招待
    inv2 = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="token_not_yours",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        max_uses=None,
        used_count=0,
    )
    db.add(inv2)
    await db.commit()

    other_token = create_access_token({"sub": str(other_user.id)})
    response = await client.delete(
        "/api/invitations/token_not_yours", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 403
