"""招待APIのテスト."""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectInvitation, TheaterProject, User


@pytest.fixture
async def test_invitation(
    db: AsyncSession, test_project: TheaterProject, test_user: User
) -> ProjectInvitation:
    """テスト用招待."""
    invitation = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="test_invitation_token",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        max_uses=10,
        used_count=0,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


@pytest.mark.asyncio
async def test_create_invitation(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """招待リンク作成のテスト."""
    # Arrange
    invitation_data = {
        "max_uses": 5,
        "expires_in_hours": 168,  # 1週間
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/invitations",
        json=invitation_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 201]
    data = response.json()
    assert "token" in data
    assert data["max_uses"] == invitation_data["max_uses"]


@pytest.mark.asyncio
async def test_get_invitation(
    client: AsyncClient,
    test_invitation: ProjectInvitation,
) -> None:
    """招待情報取得のテスト（認証不要）."""
    # Act
    response = await client.get(
        f"/api/invitations/{test_invitation.token}",
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == test_invitation.token
    assert "project_name" in data


@pytest.mark.asyncio
async def test_accept_invitation(
    client: AsyncClient,
    test_user: User,
    test_invitation: ProjectInvitation,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """招待受諾のテスト."""
    # Arrange - 新しいユーザーを作成
    new_user = User(
        discord_id="invitation_test_user",
        discord_username="invitee",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # トークン作成
    from src.auth.jwt import create_access_token
    new_user_token = create_access_token(data={"sub": str(new_user.id)})
    
    # Act
    response = await client.post(
        f"/api/invitations/{test_invitation.token}/accept",
        headers={"Authorization": f"Bearer {new_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "project_name" in data


@pytest.mark.asyncio
async def test_accept_invitation_already_member(
    client: AsyncClient,
    test_user: User,
    test_invitation: ProjectInvitation,
    test_user_token: str,
) -> None:
    """既にメンバーの場合の招待受諾テスト."""
    # Act - test_userは既にプロジェクトのオーナー
    response = await client.post(
        f"/api/invitations/{test_invitation.token}/accept",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    # 既に参加済みというメッセージまたは成功レスポンス
    assert "message" in data


@pytest.mark.asyncio
async def test_get_expired_invitation(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user: User,
) -> None:
    """期限切れ招待の取得テスト."""
    # Arrange - 期限切れの招待を作成
    expired_invitation = ProjectInvitation(
        project_id=test_project.id,
        created_by=test_user.id,
        token="expired_token",
        expires_at=datetime.now(UTC) - timedelta(days=1),  # 過去
        max_uses=10,
        used_count=0,
    )
    db.add(expired_invitation)
    await db.commit()
    
    # Act
    response = await client.get(
        f"/api/invitations/{expired_invitation.token}",
    )
    
    # Assert
    assert response.status_code in [404, 410]  # Not Found or Gone


@pytest.mark.asyncio
async def test_get_invalid_invitation(client: AsyncClient) -> None:
    """無効な招待トークンのテスト."""
    # Act
    response = await client.get(
        "/api/invitations/invalid_token_12345",
    )
    
    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_invitation_non_admin(
    client: AsyncClient,
    test_project: TheaterProject,
    db: AsyncSession,
) -> None:
    """管理者でないユーザーの招待作成テスト."""
    # Arrange - viewerロールのユーザーを作成
    viewer_user = User(
        discord_id="viewer_user_id",
        discord_username="viewer",
    )
    db.add(viewer_user)
    await db.commit()
    
    from src.db.models import ProjectMember
    member = ProjectMember(
        project_id=test_project.id,
        user_id=viewer_user.id,
        role="viewer",
    )
    db.add(member)
    await db.commit()
    
    from src.auth.jwt import create_access_token
    viewer_token = create_access_token(data={"sub": str(viewer_user.id)})
    
    invitation_data = {
        "max_uses": 5,
        "expires_in_hours": 168,
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/invitations",
        json=invitation_data,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    
    # Assert
    assert response.status_code == 403  # Permission denied
