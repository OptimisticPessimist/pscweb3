
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProjectMember, TheaterProject, User


@pytest.mark.asyncio
async def test_create_project(
    client: AsyncClient,
    test_user: User,
    test_user_token: str,
    db: AsyncSession,
):
    """プロジェクト作成テスト."""
    response = await client.post(
        "/api/projects/",
        json={"name": "Test Project", "description": "Test Description"},
        params={"token": test_user_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "Test Description"
    project_id = data["id"]

    # DB確認: プロジェクト
    project = await db.get(TheaterProject, project_id)
    assert project is not None

    # DB確認: メンバー (オーナー)
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == test_user.id,
        )
    )
    member = result.scalar_one_or_none()
    assert member is not None
    assert member.role == "owner"


@pytest.mark.asyncio
async def test_list_projects(
    client: AsyncClient,
    test_user: User,
    test_user_token: str,
    db: AsyncSession,
):
    """プロジェクト一覧取得テスト."""
    # 事前にプロジェクト作成 (既に test_create_project で作られている可能性もあるが、独立性を保つため作成)
    project = TheaterProject(name="List Test Project")
    db.add(project)
    await db.flush()
    member = ProjectMember(project_id=project.id, user_id=test_user.id, role="owner")
    db.add(member)
    await db.commit()

    response = await client.get(
        "/api/projects/",
        params={"token": test_user_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # 作成したプロジェクトが含まれているか
    project_ids = [p["id"] for p in data]
    assert project.id in project_ids


@pytest.mark.asyncio
async def test_member_management(
    client: AsyncClient,
    test_user: User,
    test_user_token: str,
    db: AsyncSession,
):
    """メンバー管理（一覧、更新、削除）テスト."""
    # 1. プロジェクト作成 (Owner: test_user)
    project = TheaterProject(name="Member Mgmt Project")
    db.add(project)
    await db.flush()
    owner_member = ProjectMember(project_id=project.id, user_id=test_user.id, role="owner")
    db.add(owner_member)
    
    # 2. 別のユーザーを作成してメンバーに追加 (Viewer)
    other_user = User(discord_id="other", discord_username="OtherUser")
    db.add(other_user)
    await db.flush()
    other_member = ProjectMember(project_id=project.id, user_id=other_user.id, role="viewer")
    db.add(other_member)
    
    await db.commit()
    
    # --- A. メンバー一覧取得 ---
    response = await client.get(
        f"/api/projects/{project.id}/members",
        params={"token": test_user_token},
    )
    assert response.status_code == 200
    members = response.json()
    assert len(members) == 2
    
    # --- B. ロール更新 (Viewer -> Editor) ---
    response = await client.put(
        f"/api/projects/{project.id}/members/{other_user.id}",
        params={"token": test_user_token},
        json={"role": "editor"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "editor"
    
    # DB確認
    await db.refresh(other_member)
    assert other_member.role == "editor"
    
    # --- C. 権限チェック (自分自身を変更しようとする -> 400) ---
    response = await client.put(
        f"/api/projects/{project.id}/members/{test_user.id}",
        params={"token": test_user_token},
        json={"role": "viewer"},
    )
    assert response.status_code == 400
    
    # --- D. メンバー削除 ---
    response = await client.delete(
        f"/api/projects/{project.id}/members/{other_user.id}",
        params={"token": test_user_token},
    )
    assert response.status_code == 200
    
    # DB確認
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == other_user.id,
        )
    )
    deleted_member = result.scalar_one_or_none()
    assert deleted_member is None
