"""データベースモデル定義."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models import CharacterCasting, NotificationSettings, ProjectMember


class User(Base):
    """ユーザーモデル（Discord OAuth連携）."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discord_username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", lazy="selectin")


class ProjectMember(Base):
    """プロジェクトメンバー（権限管理）."""

    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("theater_projects.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20))  # "owner", "editor", "viewer"
    joined_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # リレーション
    project: Mapped["TheaterProject"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_members")


class CharacterCasting(Base):
    """登場人物とユーザーの紐付け（キャスティング）.

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
    user: Mapped["User"] = relationship(back_populates="character_castings")


class NotificationSettings(Base):
    """ユーザーごとの通知設定."""

    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    re_notify_after_minutes: Mapped[int] = mapped_column(default=60)  # 再通知までの時間（分）

    # リレーション
    user: Mapped["User"] = relationship(back_populates="notification_settings")
