"""出欠JSON出力APIのテスト."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import create_access_token
from src.db.models import (
    AttendanceEvent,
    AttendanceTarget,
    ProjectMember,
    TheaterProject,
    User,
)


async def create_attendance_export_fixture(
    db: AsyncSession,
    project: TheaterProject,
) -> tuple[AttendanceEvent, User, User, User]:
    """出欠JSON出力テスト用データを作成."""
    users = [
        User(discord_id="2001", discord_username="external_a", screen_name="External Player A"),
        User(discord_id="2002", discord_username="external_b", screen_name="External Player B"),
        User(discord_id="2003", discord_username="external_c", screen_name="External Player C"),
    ]
    db.add_all(users)
    await db.flush()

    members = [
        ProjectMember(
            project_id=project.id,
            user_id=users[0].id,
            role="viewer",
            display_name="External Player A",
        ),
        ProjectMember(project_id=project.id, user_id=users[1].id, role="viewer"),
        ProjectMember(project_id=project.id, user_id=users[2].id, role="viewer"),
    ]
    db.add_all(members)

    event = AttendanceEvent(
        project_id=project.id,
        message_id="999",
        channel_id="888",
        title="イベント名",
        schedule_date=datetime(2026, 6, 27, 10, 0, tzinfo=UTC),
        deadline=datetime(2026, 6, 26, 10, 0, tzinfo=UTC),
        completed=False,
        created_at=datetime(2026, 6, 25, 10, 0, tzinfo=UTC),
    )
    db.add(event)
    await db.flush()

    db.add_all(
        [
            AttendanceTarget(event_id=event.id, user_id=users[0].id, status="ok"),
            AttendanceTarget(event_id=event.id, user_id=users[1].id, status="ng"),
            AttendanceTarget(event_id=event.id, user_id=users[2].id, status="pending"),
        ]
    )
    await db.commit()

    result = await db.execute(
        select(AttendanceEvent).where(AttendanceEvent.id == event.id)
    )
    return result.scalar_one(), users[0], users[1], users[2]


@pytest.mark.asyncio
async def test_export_attendance_event_json(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """オーナーは出欠JSONを出力できる."""
    event, *_ = await create_attendance_export_fixture(db, test_project)

    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]

    data = response.json()
    assert data["schemaVersion"] == 1
    assert data["source"] == "PSCWEB3"
    assert data["eventName"] == "イベント名"
    assert data["generatedAt"].endswith("+09:00")
    assert data["attendances"] == [
        {"name": "External Player A", "status": "出席"},
        {"name": "External Player B", "status": "欠席"},
        {"name": "External Player C", "status": "未回答"},
    ]


@pytest.mark.asyncio
async def test_export_attendance_event_allows_editor(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
) -> None:
    """編集者は出欠JSONを出力できる."""
    event, editor, *_ = await create_attendance_export_fixture(db, test_project)

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == test_project.id,
            ProjectMember.user_id == editor.id,
        )
    )
    assert member is not None
    member.role = "editor"
    await db.commit()

    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {create_access_token(data={'sub': str(editor.id)})}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_attendance_event_rejects_viewer(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
) -> None:
    """閲覧者は出欠JSONを出力できない."""
    event, viewer, *_ = await create_attendance_export_fixture(db, test_project)

    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {create_access_token(data={'sub': str(viewer.id)})}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_attendance_event_rejects_other_project(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """別プロジェクトIDでは出欠JSONを出力できない."""
    event, *_ = await create_attendance_export_fixture(db, test_project)
    other_project = TheaterProject(name="Other")
    db.add(other_project)
    await db.flush()
    owner_user_id = await db.scalar(
        select(ProjectMember.user_id).where(ProjectMember.project_id == test_project.id)
    )
    db.add(
        ProjectMember(
            project_id=other_project.id,
            user_id=owner_user_id,
            role="owner",
        )
    )
    await db.commit()

    response = await client.get(
        f"/api/projects/{other_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_attendance_event_sorts_by_name(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """出力は投入順ではなく表示名の昇順でソートされる."""
    users = [
        User(discord_id="3003", discord_username="zeta", screen_name="Zeta"),
        User(discord_id="3001", discord_username="alpha", screen_name="Alpha"),
        User(discord_id="3002", discord_username="mike", screen_name="Mike"),
    ]
    db.add_all(users)
    await db.flush()

    db.add_all(
        [
            ProjectMember(
                project_id=test_project.id,
                user_id=users[0].id,
                role="viewer",
                display_name="Zeta",
            ),
            ProjectMember(
                project_id=test_project.id,
                user_id=users[1].id,
                role="viewer",
                display_name="Alpha",
            ),
            ProjectMember(
                project_id=test_project.id,
                user_id=users[2].id,
                role="viewer",
                display_name="Mike",
            ),
        ]
    )

    event = AttendanceEvent(
        project_id=test_project.id,
        message_id="777",
        channel_id="666",
        title="ソート確認",
        schedule_date=datetime(2026, 6, 27, 10, 0, tzinfo=UTC),
        deadline=datetime(2026, 6, 26, 10, 0, tzinfo=UTC),
        completed=False,
        created_at=datetime(2026, 6, 25, 10, 0, tzinfo=UTC),
    )
    db.add(event)
    await db.flush()
    db.add_all(
        [
            AttendanceTarget(event_id=event.id, user_id=users[0].id, status="ok"),
            AttendanceTarget(event_id=event.id, user_id=users[1].id, status="ng"),
            AttendanceTarget(event_id=event.id, user_id=users[2].id, status="pending"),
        ]
    )
    await db.commit()

    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    names = [target["name"] for target in response.json()["attendances"]]
    assert names == ["Alpha", "Mike", "Zeta"]


@pytest.mark.asyncio
async def test_export_attendance_event_unknown_status_label(
    client: AsyncClient,
    db: AsyncSession,
    test_project: TheaterProject,
    test_user_token: str,
) -> None:
    """想定外のステータスは「未回答」に丸めず区別可能なラベルで出力する."""
    user = User(discord_id="4001", discord_username="legacy", screen_name="Legacy User")
    db.add(user)
    await db.flush()
    db.add(
        ProjectMember(
            project_id=test_project.id,
            user_id=user.id,
            role="viewer",
            display_name="Legacy User",
        )
    )

    event = AttendanceEvent(
        project_id=test_project.id,
        message_id="555",
        channel_id="444",
        title="未知ステータス",
        schedule_date=datetime(2026, 6, 27, 10, 0, tzinfo=UTC),
        deadline=datetime(2026, 6, 26, 10, 0, tzinfo=UTC),
        completed=False,
        created_at=datetime(2026, 6, 25, 10, 0, tzinfo=UTC),
    )
    db.add(event)
    await db.flush()
    db.add(AttendanceTarget(event_id=event.id, user_id=user.id, status="reacted"))
    await db.commit()

    response = await client.get(
        f"/api/projects/{test_project.id}/attendance/{event.id}/export",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["attendances"] == [
        {"name": "Legacy User", "status": "不明"},
    ]
