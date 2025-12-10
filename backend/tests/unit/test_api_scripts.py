"""脚本APIのテスト."""

import pytest
from httpx import AsyncClient
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Script, TheaterProject, User


@pytest.mark.asyncio
async def test_get_scripts(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """脚本一覧取得のテスト."""
    # Act
    response = await client.get(
        f"/api/scripts/{test_project.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "scripts" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_upload_script(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """脚本アップロードのテスト."""
    # Arrange
    fountain_content = """Title: Test Script
Author: Test Author

INT. TEST ROOM - DAY

A simple test script.

CHARACTER
Hello, world!
"""
    
    files = {
        "file": ("test.fountain", BytesIO(fountain_content.encode()), "text/plain")
    }
    data = {
        "title": "テスト脚本",
        "is_public": "false"
    }
    
    # Act
    response = await client.post(
        f"/api/scripts/{test_project.id}/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_get_script_detail(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """脚本詳細取得のテスト."""
    # Arrange - テスト用脚本を作成
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="詳細テスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    
    # Act
    response = await client.get(
        f"/api/scripts/{test_project.id}/{script.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(script.id)
    assert data["title"] == script.title


@pytest.mark.asyncio
async def test_get_script_scenes(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """脚本のシーン一覧取得のテスト."""
    # Arrange
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="シーンテスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    
    # Act
    response = await client.get(
        f"/api/scripts/{test_project.id}/{script.id}/scenes",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "scenes" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_get_script_characters(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
    db: AsyncSession,
) -> None:
    """脚本の登場人物一覧取得のテスト."""
    # Arrange
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="キャラクターテスト脚本",
        content="テスト内容",
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)
    
    # Act
    response = await client.get(
        f"/api/scripts/{test_project.id}/{script.id}/characters",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "characters" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_upload_script_unauthorized(
    client: AsyncClient,
    test_project: TheaterProject,
) -> None:
    """認証なしの脚本アップロードテスト."""
    # Arrange
    fountain_content = "Test content"
    files = {
        "file": ("test.fountain", BytesIO(fountain_content.encode()), "text/plain")
    }
    data = {
        "title": "Unauthorized script",
        "is_public": "false"
    }
    
    # Act
    response = await client.post(
        f"/api/scripts/{test_project.id}/upload",
        files=files,
        data=data,
    )
    
    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_script(
    client: AsyncClient,
    test_user: User,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """存在しない脚本の取得テスト."""
    # Arrange
    from uuid import uuid4
    fake_script_id = uuid4()
    
    # Act
    response = await client.get(
        f"/api/scripts/{test_project.id}/{fake_script_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    
    # Assert
    assert response.status_code == 404
