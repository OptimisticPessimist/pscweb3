"""プロジェクトAPI詳細テスト（メンバー管理・マイルストーン）."""

import pytest
from datetime import UTC, datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TheaterProject, User, ProjectMember


@pytest.fixture
async def second_user(db: AsyncSession, test_project: TheaterProject) -> User:
    """2人目のテストユーザー."""
    user = User(
        discord_id="second_user_id",
        discord_username="seconduser",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # プロジェクトメンバーとして追加
    member = ProjectMember(
        project_id=test_project.id,
        user_id=user.id,
        role="member",
    )
    db.add(member)
    await db.commit()
    
    return user


@pytest.mark.asyncio
async def test_update_member_role(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    second_user: User,
    test_user_token: str,
) -> None:
    """メンバーロール更新のテスト."""
    # Arrange
    role_update = {
        "role": "editor",
        "default_staff_role": "director",
        "display_name": "演出担当",
    }
    
    # Act
    response = await client.put(
        f"/api/projects/{test_project.id}/members/{second_user.id}",
        json=role_update,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == role_update["role"]


@pytest.mark.asyncio
async def test_remove_member(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    second_user: User,
    test_user_token: str,
) -> None:
    """メンバー削除のテスト."""
    # Act
    response = await client.delete(
        f"/api/projects/{test_project.id}/members/{second_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_milestone(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """マイルストーン作成のテスト."""
    # Arrange
    milestone_data = {
        "title": "本番公演",
        "start_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "end_date": (datetime.now(UTC) + timedelta(days=32)).isoformat(),
        " location": "劇場A",
        "color": "#FF5733",
        "create_attendance_check": False,
    }
    
    # Act
    response = await client.post(
        f"/api/projects/{test_project.id}/milestones",
        json=milestone_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_list_milestones(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """マイルストーン一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/milestones",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_milestone(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """マイルストーン削除のテスト."""
    # Arrange - マイルストーンを作成
    from src.db.models import Milestone
    milestone = Milestone(
        project_id=test_project.id,
        title="削除テスト",
        start_date=datetime.now(UTC) + timedelta(days=10),
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    
    # Act
    response = await client.delete(
        f"/api/projects/{test_project.id}/milestones/{milestone.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_member_role_self(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """自分自身のロール変更テスト（失敗すべき）."""
    # Arrange
    role_update = {
        "role": "member",  # ownerからmemberへ降格
    }
    
    # Act
    response = await client.put(
        f"/api/projects/{test_project.id}/members/{test_user.id}",
        json=role_update,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 400  # エラーになるべき


@pytest.mark.asyncio
async def test_remove_owner_self(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """オーナーの自己削除テスト（失敗すべき）."""
    # Act
    response = await client.delete(
        f"/api/projects/{test_project.id}/members/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 400  # エラーになるべき
