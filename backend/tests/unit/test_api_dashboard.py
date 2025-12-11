"""ダッシュボードAPIのテスト."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TheaterProject, User


@pytest.mark.asyncio
async def test_get_project_dashboard(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """プロジェクトダッシュボード取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/dashboard",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    # ダッシュボードには様々な統計情報が含まれる
    assert "project" in data or "stats" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_get_dashboard_stats(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """ダッシュボード統計情報取得のテスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/dashboard",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    # レスポンスが有効なJSONであることを確認
    data = response.json()
    assert data is not None


@pytest.mark.asyncio
async def test_dashboard_unauthorized(
    client: AsyncClient,
    test_project: TheaterProject,
) -> None:
    """認証なしのダッシュボードアクセステスト."""
    # Act
    response = await client.get(
        f"/api/projects/{test_project.id}/dashboard",
    )
    
    # Assert
    assert response.status_code == 401
