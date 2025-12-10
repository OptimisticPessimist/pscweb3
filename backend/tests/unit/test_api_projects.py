"""プロジェクトAPI のテスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectMember, TheaterProject, User


@pytest.mark.asyncio
async def test_create_project(
    client: AsyncClient, test_user: User, test_user_token: str
) -> None:
    """プロジェクト作成のテスト."""
    # Arrange
    project_data = {
        "name": "新しいプロジェクト",
        "description": "テスト用プロジェクト",
    }
    
    # Act
    response = await client.post(
        "/api/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(
    client: AsyncClient, test_user: User, test_project: TheaterProject, test_user_token: str
) -> None:
    """プロジェクト一覧取得のテスト."""
    # Act
    response = await client.get(
        "/api/projects/",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["id"] == str(test_project.id) for p in data)


@pytest.mark.asyncio
async def test_get_project(
    client: AsyncClient, test_user: User, test_project: TheaterProject, test_user_token: str
) -> None:
    """プロジェクト詳細取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_project.id)
    assert data["name"] == test_project.name


@pytest.mark.asyncio
async def test_update_project(
    client: AsyncClient, test_user: User, test_project: TheaterProject, test_user_token: str
) -> None:
    """プロジェクト更新のテスト."""
    # Arrange
    update_data = {
        "name": "更新されたプロジェクト名",
        "description": "更新された説明",
    }
    
    # Act
    response = await client.put(
        f"/api/projects/{test_project.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_delete_project(
    client: AsyncClient, test_user: User, test_project: TheaterProject, test_user_token: str, db: AsyncSession
) -> None:
    """プロジェクト削除のテスト."""
    # Act
    response = await client.delete(
        f"/api/projects/{test_project.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_project_members(
    client: AsyncClient, test_user: User, test_project: TheaterProject, test_user_token: str
) -> None:
    """プロジェクトメンバー一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/members",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # test_userがownerとして含まれているはず
    assert any(m["user_id"] == str(test_user.id) and m["role"] == "owner" for m in data)


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, test_project: TheaterProject) -> None:
    """認証なしのアクセステスト."""
    # Act
    response = await client.get(f"/api/projects/{test_project.id}")
    
    # Assert
    assert response.status_code == 401
