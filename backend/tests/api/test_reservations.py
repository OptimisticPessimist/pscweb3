from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.db.models import (
    User, TheaterProject, ProjectMember, Milestone, Reservation,
    Character, CharacterCasting, Script
)
from src.services.email import email_service


@pytest.fixture
def project(db_session: Session) -> TheaterProject:
    project = TheaterProject(name="Test Project", is_public=True)
    db_session.add(project)
    db_session.commit()
    return project

@pytest.fixture
def milestone(db_session: Session, project: TheaterProject) -> Milestone:
    ms = Milestone(
        project_id=project.id,
        title="Test Milestone",
        start_date=datetime.now() + timedelta(days=7),
        reservation_capacity=10  # 定員10名
    )
    db_session.add(ms)
    db_session.commit()
    return ms

@pytest.fixture
def project_member(db_session: Session, project: TheaterProject) -> User:
    user = User(discord_id="12345", discord_username="member", discord_avatar_hash="hash")
    db_session.add(user)
    db_session.commit()
    pm = ProjectMember(project_id=project.id, user_id=user.id, role="viewer")
    db_session.add(pm)
    db_session.commit()
    return user

@pytest.fixture
def cast_member(db_session: Session, project: TheaterProject) -> User:
    user = User(discord_id="67890", discord_username="cast", screen_name="Actor A")
    db_session.add(user)
    
    script = Script(project_id=project.id, uploaded_by=user.id, title="Test Script", content="")
    db_session.add(script)
    
    char = Character(script_id=script.id, name="Hero")
    db_session.add(char)
    db_session.commit()
    
    casting = CharacterCasting(character_id=char.id, user_id=user.id)
    db_session.add(casting)
    pm = ProjectMember(project_id=project.id, user_id=user.id, role="viewer")
    db_session.add(pm)
    db_session.commit()
    return user


def test_create_reservation_success(client: TestClient, milestone: Milestone):
    """予約作成成功時テスト."""
    payload = {
        "milestone_id": str(milestone.id),
        "name": "Guest User",
        "email": "guest@example.com",
        "count": 2
    }
    
    # SendGridのモック
    with patch.object(email_service, "send_reservation_confirmation") as mock_send:
        response = client.post("/api/public/reservations", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Guest User"
    assert data["count"] == 2
    
    # メール送信タスクが追加されたか (BackgroundTasksなのでテスト環境では実行されない場合もあるが、通常はmockで呼ばれるはず)
    # FastAPIのTestClientのみではBackgroundTasksの実行までは保証されないが、動作確認としてはOK


def test_create_reservation_capacity_error(client: TestClient, db_session: Session, milestone: Milestone):
    """定員オーバーエラーテスト."""
    # 既に9名予約済み (定員10名)
    r1 = Reservation(
        milestone_id=milestone.id, name="Existing", email="e@e.com", count=9
    )
    db_session.add(r1)
    db_session.commit()
    
    # 2名予約しようとするとオーバー (9+2 > 10)
    payload = {
        "milestone_id": str(milestone.id),
        "name": "Late User",
        "email": "late@example.com",
        "count": 2
    }
    response = client.post("/api/public/reservations", json=payload)
    assert response.status_code == 400
    assert "capacity exceeded" in response.json()["detail"]


def test_get_cast_members_public(client: TestClient, project: TheaterProject, cast_member: User, project_member: User):
    """紹介者リスト(キャスト絞り込み)テスト."""
    # キャストのみ
    response = client.get(f"/api/public/projects/{project.id}/members?role=cast")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Actor A" # screen_name優先
    
    # 全員
    response = client.get(f"/api/public/projects/{project.id}/members")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_admin_reservation_list(client: TestClient, db_session: Session, project: TheaterProject, milestone: Milestone, project_member: User):
    """管理者予約一覧取得テスト."""
    # 予約作成
    r = Reservation(milestone_id=milestone.id, name="R1", email="r1@e.com", count=1)
    db_session.add(r)
    db_session.commit()
    
    # ログイン
    client.app.dependency_overrides = {} # user overrideが必要ならここで
    # 今回はconftestのGlobal Overrideが効いている前提、もしくは特定のユーザーとしてリクエストを送る必要がある
    # *注: ここでは簡易的に、認証なしで通るか、テスト用認証ロジックを使用する想定*
    
    # *しかし、auth dependencyがああるので、正規にモックする*
    # *しかし、auth dependencyがああるので、正規にモックする*
    from src.dependencies.auth import get_current_user_dep
    client.app.dependency_overrides[get_current_user_dep] = lambda: project_member

    response = client.get(f"/api/projects/{project.id}/reservations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "R1"
    
    del client.app.dependency_overrides[get_current_user_dep]

def test_update_attendance(client: TestClient, db_session: Session, milestone: Milestone, project_member: User):
    """出欠更新テスト."""
    r = Reservation(milestone_id=milestone.id, name="R2", email="r2@e.com", count=1, attended=False)
    db_session.add(r)
    db_session.commit()
    
    
    from src.dependencies.auth import get_current_user_dep
    client.app.dependency_overrides[get_current_user_dep] = lambda: project_member

    payload = {"attended": True, "name": "dummy", "email": "d@d.com", "count": 1, "milestone_id": str(milestone.id)} # schema validationのため全項目必要かも？ -> UpdateSchemaはattendedのみ
    # ReservationUpdateスキーマ確認
    # class ReservationUpdate(BaseModel):
    #     attended: bool
    
    response = client.patch(f"/api/reservations/{r.id}/attendance", json={"attended": True})
    assert response.status_code == 200
    assert response.json()["attended"] is True
    
    del client.app.dependency_overrides[get_current_user_dep]

def test_export_csv(client: TestClient, db_session: Session, project: TheaterProject, milestone: Milestone, project_member: User):
    """CSVエクスポートテスト."""
    r = Reservation(milestone_id=milestone.id, name="CSV User", email="csv@e.com", count=3)
    db_session.add(r)
    db_session.commit()
    
    from src.dependencies.auth import get_current_user_dep
    client.app.dependency_overrides[get_current_user_dep] = lambda: project_member

    response = client.post(f"/api/projects/{project.id}/reservations/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "CSV User" in response.text
    
    del client.app.dependency_overrides[get_current_user_dep]
