"""データベースモデル定義."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
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
    )


class User(Base):
    """ユーザーモデル（Discord OAuth連携)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discord_username: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project_members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    character_castings: Mapped[list["CharacterCasting"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    notification_settings: Mapped["NotificationSettings | None"] = relationship(
        back_populates="user", lazy="selectin", uselist=False
    )


class TheaterProject(Base):
    """舞台プロジェクト."""

    __tablename__ = "theater_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", lazy="selectin"
    )
    scripts: Mapped[list["Script"]] = relationship(
        back_populates="project", lazy="selectin"
    )


class ProjectMember(Base):
    """プロジェクトメンバー（権限管理)."""

    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("theater_projects.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20))  # "owner", "editor", "viewer"
    joined_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_members")


class Script(Base):
    """Fountain脚本."""

    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("theater_projects.id"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))  # アップロードユーザー
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # Fountain脚本の内容を直接保存
    is_public: Mapped[bool] = mapped_column(default=False)  # 全体公開フラグ
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="scripts")
    uploader: Mapped["User"] = relationship()
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="script", lazy="selectin", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="script", lazy="selectin", cascade="all, delete-orphan"
    )
    scene_chart: Mapped["SceneChart | None"] = relationship(
        back_populates="script", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )


class Scene(Base):
    """シーン."""

    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    scene_number: Mapped[int]
    heading: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="scenes")
    lines: Mapped[list["Line"]] = relationship(
        back_populates="scene", lazy="selectin", cascade="all, delete-orphan"
    )


class Character(Base):
    """登場人物."""

    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    name: Mapped[str] = mapped_column(String(100))

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="characters")
    castings: Mapped[list["CharacterCasting"]] = relationship(
        back_populates="character", lazy="selectin"
    )
    lines: Mapped[list["Line"]] = relationship(
        back_populates="character", lazy="selectin"
    )


class Line(Base):
    """セリフ."""

    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    content: Mapped[str] = mapped_column(Text)
    order: Mapped[int]

    # リレーション
    scene: Mapped["Scene"] = relationship(back_populates="lines")
    character: Mapped["Character"] = relationship(back_populates="lines")


class SceneChart(Base):
    """香盤表."""

    __tablename__ = "scene_charts"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーション
    script: Mapped["Script"] = relationship(back_populates="scene_chart")
    mappings: Mapped[list["SceneCharacterMapping"]] = relationship(
        back_populates="chart", lazy="selectin", cascade="all, delete-orphan"
    )


class SceneCharacterMapping(Base):
    """香盤表のシーン-登場人物マッピング."""

    __tablename__ = "scene_character_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    chart_id: Mapped[int] = mapped_column(ForeignKey("scene_charts.id"))
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))

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

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cast_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "A キャスト", "B キャスト" 等

    # リレーション
    character: Mapped["Character"] = relationship(back_populates="castings")
    user: Mapped["User"] = relationship(back_populates="character_castings")


class NotificationSettings(Base):
    """ユーザーごとの通知設定."""

    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    re_notify_after_minutes: Mapped[int] = mapped_column(default=60)  # 再通知までの時間（分）

    # リレーション
    user: Mapped["User"] = relationship(back_populates="notification_settings")


class RehearsalSchedule(Base):
    """稽古スケジュール."""

    __tablename__ = "rehearsal_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("theater_projects.id"))
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship()
    script: Mapped["Script"] = relationship()
    rehearsals: Mapped[list["Rehearsal"]] = relationship(
        back_populates="schedule", lazy="selectin", cascade="all, delete-orphan"
    )


class Rehearsal(Base):
    """稽古."""

    __tablename__ = "rehearsals"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("rehearsal_schedules.id"))
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"), nullable=True)
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

    id: Mapped[int] = mapped_column(primary_key=True)
    rehearsal_id: Mapped[int] = mapped_column(ForeignKey("rehearsals.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

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

    id: Mapped[int] = mapped_column(primary_key=True)
    rehearsal_id: Mapped[int] = mapped_column(ForeignKey("rehearsals.id"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # リレーション
    rehearsal: Mapped["Rehearsal"] = relationship(back_populates="casts")
    character: Mapped["Character"] = relationship()
    user: Mapped["User"] = relationship()

    # ユニーク制約：同じ稽古で同じ役は1人のみ
    __table_args__ = (
        UniqueConstraint("rehearsal_id", "character_id", name="uq_rehearsal_character"),
    )
