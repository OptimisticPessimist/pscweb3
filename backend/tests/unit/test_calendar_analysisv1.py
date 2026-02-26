import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from src.db.models import (
    Script, Scene, Character, SceneCharacterMapping, 
    CharacterCasting, SchedulePoll, SchedulePollCandidate, 
    SchedulePollAnswer, ProjectMember
)
from src.services.schedule_poll_service import SchedulePollService

@pytest.mark.asyncio
async def test_calendar_analysis_logic(db, test_project, test_user):
    # 1. 脚本・シーン・配役のセットアップ
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Test Script",
        content="Test content"
    )
    db.add(script)
    await db.flush()

    scene = Scene(script_id=script.id, scene_number=1, heading="Scene 1")
    db.add(scene)
    await db.flush()

    char = Character(script_id=script.id, name="Hero")
    db.add(char)
    await db.flush()

    # マッピング
    mapping = SceneCharacterMapping(chart_id=script.id, scene_id=scene.id, character_id=char.id)
    db.add(mapping)

    # キャスティング
    casting = CharacterCasting(character_id=char.id, user_id=test_user.id)
    db.add(casting)

    # プロジェクトメンバー (名前取得用)
    member = ProjectMember(project_id=test_project.id, user_id=test_user.id, role="owner", display_name="Hero Member")
    db.add(member)

    # 2. 日程調整のセットアップ
    poll = SchedulePoll(project_id=test_project.id, title="Poll", creator_id=test_user.id)
    db.add(poll)
    await db.flush()

    candidate = SchedulePollCandidate(
        poll_id=poll.id, 
        start_datetime=datetime.now(timezone.utc), 
        end_datetime=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.add(candidate)
    await db.flush()

    # 3. 回答
    answer = SchedulePollAnswer(candidate_id=candidate.id, user_id=test_user.id, status="ok")
    db.add(answer)
    await db.commit()

    # 4. 分析実行
    service = SchedulePollService(db, MagicMock())
    analysis = await service.get_calendar_analysis(poll.id)

    assert analysis["poll_id"] == poll.id
    assert len(analysis["analyses"]) == 1
    
    cand_analysis = analysis["analyses"][0]
    assert cand_analysis["candidate_id"] == candidate.id
    
    # 稽古可能シーンの確認
    assert len(cand_analysis["possible_scenes"]) == 1
    assert cand_analysis["possible_scenes"][0]["scene_number"] == 1
    assert cand_analysis["possible_scenes"][0]["is_possible"] is True

@pytest.mark.asyncio
async def test_calendar_analysis_reach_logic(db, test_project, test_user):
    # 1. 脚本・シーン・配役のセットアップ
    script = Script(
        project_id=test_project.id,
        uploaded_by=test_user.id,
        title="Test Script Reach",
        content="Test content"
    )
    db.add(script)
    await db.flush()

    scene = Scene(script_id=script.id, scene_number=2, heading="Scene 2")
    db.add(scene)
    await db.flush()

    char = Character(script_id=script.id, name="Hero")
    db.add(char)
    await db.flush()

    # マッピング
    mapping = SceneCharacterMapping(chart_id=script.id, scene_id=scene.id, character_id=char.id)
    db.add(mapping)

    # キャスティング
    casting = CharacterCasting(character_id=char.id, user_id=test_user.id)
    db.add(casting)

    # プロジェクトメンバー (名前取得用)
    member = ProjectMember(project_id=test_project.id, user_id=test_user.id, role="owner", display_name="Hero Member")
    db.add(member)

    # 2. 日程調整のセットアップ
    poll = SchedulePoll(project_id=test_project.id, title="Poll Reach", creator_id=test_user.id)
    db.add(poll)
    await db.flush()

    candidate = SchedulePollCandidate(
        poll_id=poll.id, 
        start_datetime=datetime.now(timezone.utc), 
        end_datetime=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db.add(candidate)
    await db.flush()

    # 3. 回答 (NGにする)
    answer = SchedulePollAnswer(candidate_id=candidate.id, user_id=test_user.id, status="ng")
    db.add(answer)
    await db.commit()

    # 4. 分析実行
    service = SchedulePollService(db, MagicMock())
    analysis = await service.get_calendar_analysis(poll.id)
    
    cand_analysis = analysis["analyses"][0]
    
    # リーチ判定の確認
    assert len(cand_analysis["possible_scenes"]) == 0
    assert len(cand_analysis["reach_scenes"]) == 1
    assert cand_analysis["reach_scenes"][0]["scene_number"] == 2
    assert cand_analysis["reach_scenes"][0]["is_reach"] is True
    assert "Hero Member" in cand_analysis["reach_scenes"][0]["missing_user_names"]
