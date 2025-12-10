"""データベースモデル定義."""

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models import (
        Character,
        CharacterCasting,
        Line,
        NotificationSettings,
        ProjectMember,
        Rehearsal,
        RehearsalCast,
        RehearsalParticipant,
        RehearsalSchedule,
        Scene,
        SceneChart,
        SceneCharacterMapping,
        Script,
        ProjectInvitation,
        ProjectInvitation,
        AuditLog,
        Milestone,
        AttendanceEvent,
        AttendanceTarget,
    )


class User(Base):
    """ユーザーモデル（Discord OAuth連携)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    discord_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discord_username: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project_members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    character_castings: Mapped[list["CharacterCasting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_settings: Mapped["NotificationSettings | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # invitations (created_by) ? relationship not defined in User usually needed unless back_populates used.
    # checking ProjectInvitation down below, it has creator relationship.


class TheaterProject(Base):
    """舞台プロジェクト."""

    __tablename__ = "theater_projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discord_webhook_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    discord_channel_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Discord Channel ID
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    scripts: Mapped[list["Script"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["RehearsalSchedule"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["ProjectInvitation"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    
    # AuditLog has project_id but we don't strictly enforce cascade via relationship there 
    # unless we add back_populates. For now relying on DB Foreign Key or manual cleanup if needed,
    # but the Feature request didn't strictly ask for AuditLog cleanup, though it implies it.
    # Leaving AuditLog decoupled for now to avoid errors matching other side.


class ProjectMember(Base):
    """プロジェクトメンバー（権限管理)."""

    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20))  # "owner", "editor", "viewer"
    default_staff_role: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 基本的な役割（例：演出、照明）
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # プロジェクト内表示名
    joined_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_members")


class Script(Base):
    """Fountain脚本."""

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))  # アップロードユーザー
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # Fountain脚本の内容を直接保存
    is_public: Mapped[bool] = mapped_column(default=False)  # 全体公開フラグ
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    revision: Mapped[int] = mapped_column(default=1)  # リビジョン番号

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="scripts")
    uploader: Mapped["User"] = relationship()
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )
    scene_chart: Mapped["SceneChart | None"] = relationship(
        back_populates="script", uselist=False, cascade="all, delete-orphan"
    )


class Scene(Base):
    """シーン."""

    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scripts.id"))
    act_number: Mapped[int | None] = mapped_column(nullable=True)
    scene_number: Mapped[int]
    heading: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="scenes")
    lines: Mapped[list["Line"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class Character(Base):
    """登場人物."""

    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scripts.id"))
    name: Mapped[str] = mapped_column(String(100))

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="characters")
    castings: Mapped[list["CharacterCasting"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    lines: Mapped[list["Line"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class Line(Base):
    """セリフ."""

    __tablename__ = "lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenes.id"))
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    content: Mapped[str] = mapped_column(Text)
    order: Mapped[int]

    # リレーション
    scene: Mapped["Scene"] = relationship(back_populates="lines")
    character: Mapped["Character"] = relationship(back_populates="lines")



class SceneChart(Base):
    """香盤表."""

    __tablename__ = "scene_charts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scripts.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="scene_chart")
    mappings: Mapped[list["SceneCharacterMapping"]] = relationship(
        back_populates="chart", cascade="all, delete-orphan"
    )


class SceneCharacterMapping(Base):
    """香盤表のシーン-登場人物マッピング."""

    __tablename__ = "scene_character_mappings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    chart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scene_charts.id"))
    scene_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenes.id"))
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))

    # リレーション
    chart: Mapped["SceneChart"] = relationship(back_populates="mappings")
    scene: Mapped["Scene"] = relationship()
    character: Mapped["Character"] = relationship()

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("chart_id", "scene_id", "character_id", name="uq_chart_scene_character"),
    )


class CharacterCasting(Base):
    """登場人物とユーザーの紐付け（キャスティング).

    ダブルキャスト対応：同一の character_id に対して複数の user_id を登録可能。
    """

    __tablename__ = "character_castings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    cast_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "Pattern A", "Pattern B", "Memo" etc.

    # リレーション
    character: Mapped["Character"] = relationship(back_populates="castings")
    user: Mapped["User"] = relationship(back_populates="character_castings")


class NotificationSettings(Base):
    """ユーザーごとの通知設定."""

    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    re_notify_after_minutes: Mapped[int] = mapped_column(default=60)  # 再通知までの時間（分）

    # リレーション
    user: Mapped["User"] = relationship(back_populates="notification_settings")


class RehearsalSchedule(Base):
    """稽古スケジュール."""

    __tablename__ = "rehearsal_schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    script_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scripts.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="schedules")
    script: Mapped["Script"] = relationship()
    rehearsals: Mapped[list["Rehearsal"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )


class Rehearsal(Base):
    """稽古."""

    __tablename__ = "rehearsals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rehearsal_schedules.id"))
    scene_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(default=120)  # 稽古時間（分）
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # リレーション
    schedule: Mapped["RehearsalSchedule"] = relationship(back_populates="rehearsals")
    scene: Mapped["Scene | None"] = relationship()
    participants: Mapped[list["RehearsalParticipant"]] = relationship(
        back_populates="rehearsal", lazy="selectin", cascade="all, delete-orphan"
    )
    casts: Mapped[list["RehearsalCast"]] = relationship(
        back_populates="rehearsal", lazy="selectin", cascade="all, delete-orphan"
    )


class RehearsalParticipant(Base):
    """稽古参加者."""

    __tablename__ = "rehearsal_participants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rehearsal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rehearsals.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    staff_role: Mapped[str | None] = mapped_column(String(100), nullable=True)  # その稽古での役割

    # リレーション
    rehearsal: Mapped["Rehearsal"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("rehearsal_id", "user_id", name="uq_rehearsal_user"),
    )


class RehearsalCast(Base):
    """稽古ごとのキャスト指定."""

    __tablename__ = "rehearsal_casts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rehearsal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rehearsals.id"))
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    # リレーション
    rehearsal: Mapped["Rehearsal"] = relationship(back_populates="casts")
    character: Mapped["Character"] = relationship()
    user: Mapped["User"] = relationship()

    # ユニーク制約：同じ稽古で同じ役は1人のみ
    __table_args__ = (
        UniqueConstraint("rehearsal_id", "character_id", name="uq_rehearsal_character"),
    )


class ProjectInvitation(Base):
    """プロジェクト招待トークン."""

    __tablename__ = "project_invitations"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[int | None] = mapped_column(default=None)  # Noneなら無制限
    used_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="invitations")
    creator: Mapped["User"] = relationship()


class AuditLog(Base):
    """監査ログ."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event: Mapped[str] = mapped_column(String(100))  # イベント名 (e.g. "project.create")
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("theater_projects.id"), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON形式の詳細情報
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    user: Mapped["User | None"] = relationship()
    project: Mapped["TheaterProject | None"] = relationship(back_populates="audit_logs")


class Milestone(Base):
    """プロジェクトのマイルストーン（本番、GP、小屋入りなど）."""

    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    title: Mapped[str] = mapped_column(String(200))  # "本番初日", "顔合わせ"
    start_date: Mapped[datetime] = mapped_column(DateTime)  # 日時
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 終了日時（任意）
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # HEX colorカレンダー表示用の色コード (e.g. "#FF0000")

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="milestones")

class AttendanceEvent(Base):
    """出欠確認イベント."""

    __tablename__ = "attendance_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theater_projects.id"))
    message_id: Mapped[str] = mapped_column(String(50))  # Discord Message ID
    channel_id: Mapped[str] = mapped_column(String(50))  # Discord Channel ID
    title: Mapped[str] = mapped_column(String(200))  # イベント名
    schedule_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 稽古日時
    deadline: Mapped[datetime] = mapped_column(DateTime)  # 回答期限
    completed: Mapped[bool] = mapped_column(default=False)  # 完了フラグ
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship()
    targets: Mapped[list["AttendanceTarget"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class AttendanceTarget(Base):
    """出欠確認対象者."""

    __tablename__ = "attendance_targets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attendance_events.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, reacted, reminded

    # リレーション
    event: Mapped["AttendanceEvent"] = relationship(back_populates="targets")
    user: Mapped["User"] = relationship()

    # ユニーク制約
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_attendance_event_user"),
    )
