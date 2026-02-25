"""日程調整サービス."""

from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from src.db.models import (
    SchedulePoll, 
    SchedulePollCandidate, 
    SchedulePollAnswer, 
    TheaterProject, 
    ProjectMember, 
    CharacterCasting, 
    SceneCharacterMapping, 
    Scene,
    User,
    Script
)
from src.config import settings
from src.services.discord import DiscordService

logger = get_logger(__name__)


class SchedulePollService:
    """日程調整のビジネスロジック."""

    def __init__(self, db: AsyncSession, discord_service: DiscordService) -> None:
        self.db = db
        self.discord_service = discord_service

    async def create_poll(
        self,
        project: TheaterProject,
        title: str,
        description: Optional[str],
        candidates_data: list[dict],
        creator_id: uuid.UUID
    ) -> SchedulePoll:
        """日程調整を作成し、Discordに送信."""
        poll_id = uuid.uuid4()
        
        poll = SchedulePoll(
            id=poll_id,
            project_id=project.id,
            title=title,
            description=description,
            creator_id=creator_id,
            is_closed=False
        )
        self.db.add(poll)
        
        candidates = []
        for c_data in candidates_data:
            candidate = SchedulePollCandidate(
                id=uuid.uuid4(),
                poll_id=poll_id,
                start_datetime=c_data["start_datetime"],
                end_datetime=c_data["end_datetime"]
            )
            candidates.append(candidate)
            self.db.add(candidate)
        
        await self.db.flush()

        # Discord通知
        if project.discord_channel_id:
            logger.info("Sending schedule poll to Discord", project_id=project.id, channel_id=project.discord_channel_id)
            
            # メッセージ構築
            message_content = (
                f"**【日程調整】{title}**\n"
            )
            if description:
                message_content += f"{description}\n"
            
            message_content += "\n（※以下のボタンから回答するか、Webフォームを開いて回答してください）\n"
            
            components = []
            
            # 5日程以内の場合は行ごとのボタンを表示
            if len(candidates) <= 5:
                for i, c in enumerate(candidates):
                    # 日本時間に変換して表示 (UTC -> JST)
                    jst = timezone(timedelta(hours=9))
                    start_jst = c.start_datetime.astimezone(jst)
                    start_str = start_jst.strftime("%m/%d %H:%M")
                    row = {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 2, # Secondary
                                "label": f"{i+1}. {start_str}",
                                "custom_id": f"poll_noop:{c.id}",
                                "disabled": True
                            },
                            {
                                "type": 2,
                                "style": 3, # Success
                                "label": "〇",
                                "custom_id": f"poll_answer:{c.id}:ok"
                            },
                            {
                                "type": 2,
                                "style": 1, # Primary
                                "label": "△",
                                "custom_id": f"poll_answer:{c.id}:maybe"
                            },
                            {
                                "type": 2,
                                "style": 4, # Danger
                                "label": "×",
                                "custom_id": f"poll_answer:{c.id}:ng"
                            }
                        ]
                    }
                    components.append(row)
            
            # Webフォームへのリンクボタン (Action Row)
            base_url = settings.frontend_url or "https://pscweb3.azurewebsites.net"
            web_url = f"{base_url}/projects/{project.id}/polls/{poll_id}"
            
            web_row = {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5, # Link
                        "label": "🌐 Webフォームを開いて一括回答する",
                        "url": web_url
                    }
                ]
            }
            components.append(web_row)

            discord_resp = await self.discord_service.send_channel_message(
                channel_id=project.discord_channel_id,
                content=message_content,
                components=components
            )
            
            if discord_resp:
                poll.message_id = discord_resp.get("id")
                poll.channel_id = project.discord_channel_id

        await self.db.commit()
        return await self.get_poll_with_details(poll_id)

    async def get_poll_with_details(self, poll_id: uuid.UUID) -> Optional[SchedulePoll]:
        """詳細情報付きで日程調整を取得."""
        stmt = (
            select(SchedulePoll)
            .where(SchedulePoll.id == poll_id)
            .options(
                selectinload(SchedulePoll.candidates)
                .selectinload(SchedulePollCandidate.answers)
                .selectinload(SchedulePollAnswer.user)
            )
        )
        result = await self.db.execute(stmt)
        poll = result.scalar_one_or_none()
        if not poll:
            return None
            
        # メンバーの表示名を取得
        member_stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id)
        member_result = await self.db.execute(member_stmt)
        name_map = {m.user_id: m.display_name for m in member_result.scalars().all()}
        
        # 回答情報を補完
        for candidate in poll.candidates:
            for answer in candidate.answers:
                # Pydanticが拾えるように属性をセット
                answer.display_name = name_map.get(answer.user_id)
                answer.discord_username = answer.user.discord_username if answer.user else None
        
        return poll

    async def upsert_answer(self, candidate_id: uuid.UUID, user_id: uuid.UUID, status: str):
        """回答を登録/更新."""
        stmt = select(SchedulePollAnswer).where(
            SchedulePollAnswer.candidate_id == candidate_id,
            SchedulePollAnswer.user_id == user_id
        )
        result = await self.db.execute(stmt)
        answer = result.scalar_one_or_none()
        
        if answer:
            answer.status = status
        else:
            answer = SchedulePollAnswer(
                candidate_id=candidate_id,
                user_id=user_id,
                status=status
            )
            self.db.add(answer)
        
        await self.db.commit()

    async def get_recommendations(self, poll_id: uuid.UUID):
        """優先度アルゴリズムに基づくレコメンドを取得."""
        poll = await self.get_poll_with_details(poll_id)
        if not poll:
            return []
        
        # プロジェクトの最新の脚本を対象とする
        script_stmt = select(Script).where(Script.project_id == poll.project_id).order_by(Script.revision.desc()).limit(1)
        script_result = await self.db.execute(script_stmt)
        script = script_result.scalar_one_or_none()
        
        if not script:
            return []
        
        # シーンごとの必須ユーザーIDセットを作成
        mapping_stmt = select(SceneCharacterMapping).join(SceneCharacterMapping.scene).where(Scene.script_id == script.id)
        mapping_result = await self.db.execute(mapping_stmt)
        mappings = mapping_result.scalars().all()
        
        scene_required_users = {} # {scene_id: set(user_id)}
        for m in mappings:
            if m.scene_id not in scene_required_users:
                scene_required_users[m.scene_id] = set()
            
            cast_stmt = select(CharacterCasting).where(CharacterCasting.character_id == m.character_id)
            cast_result = await self.db.execute(cast_stmt)
            for casting in cast_result.scalars().all():
                scene_required_users[m.scene_id].add(casting.user_id)

        # 優先メンバー
        priority_member_stmt = select(ProjectMember).where(
            ProjectMember.project_id == poll.project_id,
            ProjectMember.default_staff_role.in_(["演出", "演出助手", "制作"])
        )
        priority_result = await self.db.execute(priority_member_stmt)
        priority_user_ids = {m.user_id for m in priority_result.scalars().all()}

        recommendations = []
        for candidate in poll.candidates:
            user_answers = {a.user_id: a.status for a in candidate.answers}
            
            possible_scenes = []
            for scene_id, required_user_ids in scene_required_users.items():
                is_possible = True
                for rid in required_user_ids:
                    status = user_answers.get(rid, "pending")
                    if status == "ng":
                        is_possible = False
                        break
                
                if is_possible and required_user_ids:
                    score = 0
                    for rid in required_user_ids:
                        if user_answers.get(rid) == "ok": score += 10
                        elif user_answers.get(rid) == "maybe": score += 5
                    
                    for pid in priority_user_ids:
                        if user_answers.get(pid) == "ok": score += 20
                        elif user_answers.get(pid) == "maybe": score += 10
                    
                    possible_scenes.append({
                        "scene_id": scene_id,
                        "score": score
                    })
            
            possible_scenes.sort(key=lambda x: x["score"], reverse=True)
            
            recommendations.append({
                "candidate_id": candidate.id,
                "start_datetime": candidate.start_datetime,
                "end_datetime": candidate.end_datetime,
                "possible_scenes": possible_scenes[:5]
            })
            
        return recommendations


def get_schedule_poll_service(db: AsyncSession, discord_service: DiscordService) -> SchedulePollService:
    return SchedulePollService(db, discord_service)
