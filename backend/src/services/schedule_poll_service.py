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
    Script,
    Character
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
        creator_id: uuid.UUID,
        required_roles: list[str] | None = None,
        deadline: datetime | None = None
    ) -> SchedulePoll:
        """日程調整を作成し、Discordに送信."""
        poll_id = uuid.uuid4()
        
        # 役職リストをカンマ区切り文字列に変換
        required_roles_str = ",".join(required_roles) if required_roles else None

        poll = SchedulePoll(
            id=poll_id,
            project_id=project.id,
            title=title,
            description=description,
            creator_id=creator_id,
            is_closed=False,
            required_roles=required_roles_str,
            deadline=deadline
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
            
            # メンバー属性（Discord ID）を取得するためにクエリ
            stmt = select(ProjectMember).where(ProjectMember.project_id == project.id).options(selectinload(ProjectMember.user))
            result = await self.db.execute(stmt)
            all_members = result.scalars().all()

            # メンション対象の抽出（全メンバー）
            mentions = []
            for m in all_members:
                if m.user.discord_id:
                    mentions.append(f"<@{m.user.discord_id}>")
            
            mention_str = " ".join(mentions) if mentions else ""

            # メッセージ構築
            message_content = ""
            if mention_str:
                message_content += f"{mention_str}\n\n"
            
            message_content += f"**【日程調整】{title}**\n"
            if description:
                message_content += f"{description}\n"
            
            message_content += "\n（※以下のボタンから回答するか、Webフォームを開いて回答してください）\n"
            
            components = []
            
            # 5日程以内の場合は行ごとのボタンを表示
            # 5日程以内の場合は詳細をメッセージに含める
            if len(candidates) <= 5:
                message_content += "\n**【候補日時】**\n"
                for i, c in enumerate(candidates):
                    # 内容には動的タイムスタンプを使用して、表示側のタイムゾーンに合わせる
                    ts = int(c.start_datetime.timestamp())
                    message_content += f"{i+1}. <t:{ts}:F>\n"
                    
                    # ボタンラベル用（JST固定）
                    jst_time = c.start_datetime.astimezone(timezone(timedelta(hours=9)))
                    start_str_label = jst_time.strftime("%m/%d(%a) %H:%M")
                    
                    row = {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 2, # Secondary
                                "label": f"{i+1}. {start_str_label}",
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
            
        # メンバーの表示名と役職を取得
        member_stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id)
        member_result = await self.db.execute(member_stmt)
        members = member_result.scalars().all()
        name_map = {m.user_id: m.display_name for m in members}
        staff_role_map = {m.user_id: m.default_staff_role for m in members}
        
        # 配役の取得（最新の脚本に基づく）
        script_stmt = select(Script).where(Script.project_id == poll.project_id).order_by(Script.revision.desc()).limit(1)
        script_result = await self.db.execute(script_stmt)
        script = script_result.scalar_one_or_none()
        
        cast_map = {}
        if script:
            cast_stmt = select(CharacterCasting).join(CharacterCasting.character).where(Character.script_id == script.id).options(selectinload(CharacterCasting.character))
            cast_result = await self.db.execute(cast_stmt)
            for casting in cast_result.scalars().all():
                if casting.user_id not in cast_map:
                    cast_map[casting.user_id] = []
                cast_map[casting.user_id].append(casting.character.name)
        
        # 回答情報を補完
        for candidate in poll.candidates:
            for answer in candidate.answers:
                # Pydanticが拾えるように属性をセット
                answer.display_name = name_map.get(answer.user_id)
                answer.discord_username = answer.user.display_name if answer.user else None
                
                roles = []
                staff_role = staff_role_map.get(answer.user_id)
                if staff_role:
                    roles.append(staff_role)
                
                casts = cast_map.get(answer.user_id)
                if casts:
                    roles.extend(casts)
                    
                answer.role = " / ".join(roles) if roles else None
        
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
        
        # 脚本が設定されていない場合のフォールバック（全体出席数に基づく）
        if not script:
            recommendations = []
            for candidate in poll.candidates:
                ok_count = sum(1 for a in candidate.answers if a.status == "ok")
                maybe_count = sum(1 for a in candidate.answers if a.status == "maybe")
                score = ok_count * 10 + maybe_count * 5
                
                if score > 0 or not candidate.answers:
                    recommendations.append({
                        "candidate_id": candidate.id,
                        "start_datetime": candidate.start_datetime,
                        "end_datetime": candidate.end_datetime,
                        "possible_scenes": [],
                        "reason": f"出席可能者: {ok_count}名" if ok_count > 0 else "稽古可能なメンバーがいます"
                    })
            recommendations.sort(key=lambda x: (sum(1 for a in [c for c in poll.candidates if c.id == x["candidate_id"]][0].answers if a.status == "ok")), reverse=True)
            return recommendations[:3]
        
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

        # プロジェクトメンバー全員を取得して役職マップを作成
        all_members_stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id)
        all_members = (await self.db.execute(all_members_stmt)).scalars().all()
        role_users = {}
        for m in all_members:
            if m.default_staff_role:
                if m.default_staff_role not in role_users:
                    role_users[m.default_staff_role] = []
                role_users[m.default_staff_role].append(m.user_id)

        # 必須役職（あれば）
        required_roles = []
        if poll.required_roles:
            required_roles = [r.strip() for r in poll.required_roles.split(",") if r.strip()]

        # 優先メンバー（スコア計算用）
        if required_roles:
            priority_user_ids = set()
            for role in required_roles:
                priority_user_ids.update(role_users.get(role, []))
        else:
            # 従来通りのデフォルト優先メンバー
            priority_user_ids = {m.user_id for m in all_members if m.default_staff_role in ["演出", "演出助手", "制作"]}

        # シーン情報を取得
        scene_stmt = select(Scene).where(Scene.script_id == script.id)
        scene_result = await self.db.execute(scene_stmt)
        scenes_map = {s.id: s for s in scene_result.scalars().all()}

        recommendations = []
        for candidate in poll.candidates:
            user_answers = {a.user_id: a.status for a in candidate.answers}
            ok_count_total = sum(1 for a in candidate.answers if a.status == "ok")
            maybe_count_total = sum(1 for a in candidate.answers if a.status == "maybe")
            
            # 必須役職のNGチェック
            missing_roles = []
            for role in required_roles:
                r_users = role_users.get(role, [])
                if r_users and all(user_answers.get(uid) == "ng" for uid in r_users):
                    missing_roles.append(role)

            candidate_possible_scenes = []
            for scene_id, required_user_ids in scene_required_users.items():
                is_possible = True
                if missing_roles:
                    is_possible = False
                else:
                    for rid in required_user_ids:
                        status = user_answers.get(rid, "pending")
                        if status == "ng":
                            is_possible = False
                            break
                
                if is_possible and required_user_ids:
                    score = 0
                    ok_count = 0
                    for rid in required_user_ids:
                        if user_answers.get(rid) == "ok":
                            score += 10
                            ok_count += 1
                        elif user_answers.get(rid) == "maybe":
                            score += 5
                    
                    priority_ok = False
                    for pid in priority_user_ids:
                        if user_answers.get(pid) == "ok":
                            score += 20
                            priority_ok = True
                        elif user_answers.get(pid) == "maybe":
                            score += 10
                    
                    scene = scenes_map.get(scene_id)
                    if scene:
                        reason_parts = []
                        if ok_count == len(required_user_ids):
                            reason_parts.append("必須キャスト全員出席可能")
                        elif ok_count > 0:
                            reason_parts.append(f"必須キャスト{ok_count}名出席可能")
                        
                        if priority_ok:
                            reason_parts.append("演出・制作メンバー出席可能")
                            
                        candidate_possible_scenes.append({
                            "scene_id": scene_id,
                            "scene_number": scene.scene_number,
                            "scene_heading": scene.heading,
                            "score": score,
                            "reason": " / ".join(reason_parts)
                        })
            
            candidate_possible_scenes.sort(key=lambda x: x["score"], reverse=True)
            
            # 理由の決定
            if candidate_possible_scenes:
                top_scene = candidate_possible_scenes[0]
                summary_reason = top_scene["reason"] or "稽古可能なシーンあり"
            else:
                if missing_roles:
                    summary_reason = f"不足役職: {', '.join(missing_roles)}"
                else:
                    summary_reason = f"出席可能者: {ok_count_total}名" if ok_count_total > 0 else "稽古可能なメンバーがいます"

            # スコアの決定（シーンスコアがあればそれ、なければ全体出席数ベース）
            total_score = candidate_possible_scenes[0]["score"] if candidate_possible_scenes else (ok_count_total * 5)
            if missing_roles:
                total_score = 0

            if total_score > 0 or not candidate.answers:
                recommendations.append({
                    "candidate_id": candidate.id,
                    "start_datetime": candidate.start_datetime,
                    "end_datetime": candidate.end_datetime,
                    "possible_scenes": candidate_possible_scenes[:5],
                    "reason": summary_reason,
                    "score": total_score
                })
            
        # おすすめ度順にソート（上位3件）
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:3]

    async def get_calendar_analysis(self, poll_id: uuid.UUID):
        """カレンダー表示用の詳細分析（正引き・リーチ判定込）."""
        poll = await self.get_poll_with_details(poll_id)
        if not poll:
            return None
        
        # 1. データの準備
        script_stmt = select(Script).where(Script.project_id == poll.project_id).order_by(Script.revision.desc()).limit(1)
        script = (await self.db.execute(script_stmt)).scalar_one_or_none()
        if not script:
            return {"poll_id": poll_id, "analyses": []}

        # シーン一覧
        scenes_stmt = select(Scene).where(Scene.script_id == script.id).order_by(Scene.scene_number)
        scenes = (await self.db.execute(scenes_stmt)).scalars().all()

        # シーンごとの必要キャラクター
        mapping_stmt = select(SceneCharacterMapping).where(SceneCharacterMapping.chart_id.in_(
            select(Script.id).where(Script.project_id == poll.project_id) # 香盤表はScriptに紐付いている前提
        ))
        # 実際には SceneCharacterMapping は scene_id に紐付いているのでそちらで。
        mapping_stmt = select(SceneCharacterMapping).join(Scene).where(Scene.script_id == script.id)
        mappings = (await self.db.execute(mapping_stmt)).scalars().all()
        
        scene_chars = {} # {scene_id: [character_id]}
        for m in mappings:
            if m.scene_id not in scene_chars:
                scene_chars[m.scene_id] = []
            scene_chars[m.scene_id].append(m.character_id)

        # キャラクターごとのキャスト（ユーザーID）
        casting_stmt = select(CharacterCasting).join(Character).where(Character.script_id == script.id).options(selectinload(CharacterCasting.character))
        castings = (await self.db.execute(casting_stmt)).scalars().all()
        
        char_users = {} # {character_id: [user_id]}
        user_names = {} # {user_id: name}
        char_name_map = {} # {character_id: name}
        
        # ユーザー名取得用
        all_member_stmt = select(ProjectMember).where(ProjectMember.project_id == poll.project_id)
        members = (await self.db.execute(all_member_stmt)).scalars().all()
        user_names = {m.user_id: (m.display_name or f"User {str(m.user_id)[:8]}") for m in members}

        for c in castings:
            if c.character_id not in char_users:
                char_users[c.character_id] = []
            char_users[c.character_id].append(c.user_id)
            char_name_map[c.character_id] = c.character.name

        # 必須役職の抽出
        required_roles = []
        if poll.required_roles:
            required_roles = [r.strip() for r in poll.required_roles.split(",") if r.strip()]

        # 役職ごとのユーザーマップ
        role_users = {} # {role: [user_id]}
        user_roles = {} # {user_id: str}
        for m in members:
            roles = []
            if m.default_staff_role:
                roles.append(m.default_staff_role)
                if m.default_staff_role not in role_users:
                    role_users[m.default_staff_role] = []
                role_users[m.default_staff_role].append(m.user_id)
            user_roles[m.user_id] = roles

        # 配役情報の追加
        for c in castings:
            if c.user_id in user_roles:
                user_roles[c.user_id].append(c.character.name)

        # 2. 各候補日程の分析
        analyses = []
        for candidate in poll.candidates:
            # OK/Maybe ユーザーの抽出
            available_users = {a.user_id for a in candidate.answers if a.status in ["ok", "maybe"]}
            maybe_users = {a.user_id for a in candidate.answers if a.status == "maybe"}
            
            # 必須役職のチェック
            missing_roles = []
            for role in required_roles:
                r_users = role_users.get(role, [])
                if not any(uid in available_users for uid in r_users):
                    missing_roles.append(role)

            possible_scenes = []
            reach_scenes = []
            
            for scene in scenes:
                req_chars = scene_chars.get(scene.id, [])
                if not req_chars:
                    continue
                
                missing_chars = [] # [(char_name, [missing_user_ids])]
                
                for char_id in req_chars:
                    c_users = char_users.get(char_id, [])
                    # ダブルキャスト対応：1人でも利用可能ならOK
                    if not any(uid in available_users for uid in c_users):
                        char_name = char_name_map.get(char_id, "Unknown")
                        missing_chars.append((char_name, c_users))
                
                if not missing_chars and not missing_roles:
                    # 稽古可能
                    possible_scenes.append({
                        "scene_id": scene.id,
                        "scene_number": scene.scene_number,
                        "heading": scene.heading,
                        "is_possible": True,
                        "reason": "全員揃っています"
                    })
                elif not missing_roles and len(missing_chars) == 1:
                    # リーチ状態（あと1役だけ足りない）
                    char_name, m_uids = missing_chars[0]
                    reach_scenes.append({
                        "scene_id": scene.id,
                        "scene_number": scene.scene_number,
                        "heading": scene.heading,
                        "is_possible": False,
                        "is_reach": True,
                        "missing_user_names": [user_names.get(uid, "未配役") for uid in m_uids],
                        "reason": f"不足: {char_name}"
                    })
                elif missing_roles:
                    # 必須役職が足りない場合、リーチ判定にも含めないか、理由に役職不足を書く
                    # 今回は「役職不足」としてリーチには入れない（役者が揃っていても不可能なので）
                    pass
            
            # メンバー詳細情報の構築
            available_members = []
            maybe_members = []
            for uid in available_users:
                name = user_names.get(uid, "Unknown")
                roles_list = user_roles.get(uid, [])
                role_str = " / ".join(roles_list) if roles_list else None
                member_info = {
                    "user_id": uid,
                    "name": name,
                    "role": role_str
                }
                available_members.append(member_info)
                if uid in maybe_users:
                    maybe_members.append(member_info)

            analyses.append({
                "candidate_id": candidate.id,
                "start_datetime": candidate.start_datetime,
                "end_datetime": candidate.end_datetime,
                "possible_scenes": possible_scenes,
                "reach_scenes": reach_scenes,
                "available_users": list(available_users),
                "maybe_users": list(maybe_users),
                "available_user_names": [user_names.get(uid, "Unknown") for uid in available_users],
                "maybe_user_names": [user_names.get(uid, "Unknown") for uid in maybe_users],
                "available_members": available_members,
                "maybe_members": maybe_members,
            })
        all_scenes_info = [
            {
                "scene_id": s.id,
                "scene_number": s.scene_number,
                "heading": s.heading
            }
            for s in scenes
        ]

        return {"poll_id": poll_id, "all_scenes": all_scenes_info, "analyses": analyses}

    async def get_unanswered_members(self, poll_id: uuid.UUID) -> list[dict]:
        """未回答メンバーのリストを取得."""
        stmt = (
            select(SchedulePoll)
            .where(SchedulePoll.id == poll_id)
            .options(
                selectinload(SchedulePoll.candidates)
                .selectinload(SchedulePollCandidate.answers)
            )
        )
        result = await self.db.execute(stmt)
        poll = result.scalar_one_or_none()
        if not poll:
            return []

        # 回答済みのユーザーIDを収集
        answered_user_ids = set()
        for candidate in poll.candidates:
            for answer in candidate.answers:
                answered_user_ids.add(answer.user_id)

        # プロジェクトメンバー全員を取得
        member_stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == poll.project_id)
            .options(selectinload(ProjectMember.user))
        )
        member_result = await self.db.execute(member_stmt)
        members = member_result.scalars().all()

        unanswered = []
        for m in members:
            if m.user_id not in answered_user_ids:
                unanswered.append({
                    "user_id": m.user_id,
                    "name": m.display_name or (m.user.display_name if m.user else "Unknown"),
                    "role": m.default_staff_role,
                    "discord_id": m.user.discord_id if m.user else None
                })
        
        return unanswered

    async def send_reminder(self, poll_id: uuid.UUID, target_user_ids: list[uuid.UUID], base_url: str):
        """未回答メンバーにDiscordリマインドを送信."""
        stmt = select(SchedulePoll).where(SchedulePoll.id == poll_id)
        result = await self.db.execute(stmt)
        poll = result.scalar_one_or_none()
        if not poll:
            return

        project = await self.db.get(TheaterProject, poll.project_id)
        if not project:
            return

        # ターゲットユーザーのDiscord IDを取得
        user_stmt = select(User).where(User.id.in_(target_user_ids))
        user_result = await self.db.execute(user_stmt)
        users = user_result.scalars().all()
        
        mentions = [f"<@{u.discord_id}>" for u in users if u.discord_id]
        if not mentions:
            return

        web_url = f"{base_url}/projects/{project.id}/polls/{poll_id}"
        
        content = (
            f"🔔 **【日程調整リマインド】**\n"
            f"「**{poll.title}**」の回答がまだの方がいらっしゃいます。お手数ですが回答をお願いします！\n\n"
            f"{' '.join(mentions)}\n\n"
            f"🌐 {web_url}"
        )

        if project.discord_webhook_url:
            await self.discord_service.send_notification(
                content=content,
                webhook_url=project.discord_webhook_url
            )
        elif project.discord_channel_id:
            await self.discord_service.send_channel_message(
                channel_id=project.discord_channel_id,
                content=content
            )

    async def stop_auto_reminder(self, poll_id: uuid.UUID) -> bool:
        """自動リマインドを停止する."""
        poll = await self.db.get(SchedulePoll, poll_id)
        if not poll:
            return False
        
        poll.auto_reminder_stopped = True
        await self.db.commit()
        return True

    async def check_poll_deadlines(self, base_url: str) -> dict[str, int]:
        """期限が過ぎた日程調整の自動リマインドをチェックして送信."""
        stats = {"checked_polls": 0, "reminders_sent": 0, "errors": 0}
        now = datetime.now(timezone.utc)

        # 期限が過ぎており、未リマインドかつ停止されていない、未完了のPollを取得
        stmt = (
            select(SchedulePoll)
            .where(
                SchedulePoll.deadline.is_not(None),
                SchedulePoll.deadline <= now,
                SchedulePoll.reminder_sent_at.is_(None),
                SchedulePoll.auto_reminder_stopped == False,
                SchedulePoll.is_closed == False
            )
            .options(selectinload(SchedulePoll.project))
        )
        
        result = await self.db.execute(stmt)
        polls = result.scalars().all()
        stats["checked_polls"] = len(polls)

        for poll in polls:
            try:
                # 未回答メンバーを取得
                unanswered = await self.get_unanswered_members(poll.id)
                if unanswered:
                    target_user_ids = [u["user_id"] for u in unanswered]
                    await self.send_reminder(poll.id, target_user_ids, base_url)
                    stats["reminders_sent"] += 1
                
                # 送信済みとしてマーク（未回答者がいない場合も、今後送らないようにマーク）
                poll.reminder_sent_at = now
            except Exception as e:
                logger.error(f"Error sending auto reminder for poll {poll.id}: {e}", poll_id=poll.id)
                stats["errors"] += 1
        
        await self.db.commit()
        return stats


def get_schedule_poll_service(db: AsyncSession, discord_service: DiscordService) -> SchedulePollService:
    return SchedulePollService(db, discord_service)
