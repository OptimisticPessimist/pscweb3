"""pytest設定とフィクスチャ."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.models import ProjectMember, TheaterProject, User

# テスト用データベースURL（aiosqlite使用）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """イベントループフィクスチャ."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッションフィクスチャ."""
    # テスト用エンジン作成
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # セッション作成
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """テスト用ユーザーフィクスチャ."""
    user = User(
        discord_id="123456789",
        discord_username="testuser",
        email="test@example.com",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_project(db: AsyncSession, test_user: User) -> TheaterProject:
    """テスト用プロジェクトフィクスチャ."""
    project = TheaterProject(
        name="テスト舞台プロジェクト",
        description="テスト用の舞台プロジェクト",
    )
    db.add(project)
    await db.flush()

    # プロジェクトメンバーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()
    await db.refresh(project)

    return project
