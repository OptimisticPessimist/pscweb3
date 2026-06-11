"""Converge legacy migration-built environments with the ORM models.

このリビジョンより前の履歴を適用済みの既存環境は、過去のマイグレーションを
再実行しないため、後付けでモデルに追加された列が反映されない。本リビジョンは
それらの欠落列を冪等に補い、スキーマをモデルへ収束させる。

対象列:
- theater_projects.is_public
- project_members.display_name
- scripts.public_terms
- scripts.public_contact
- schedule_polls.required_roles
- attendance_events.schedule_date

すべて ``ADD COLUMN IF NOT EXISTS`` を用いるため、列が既に存在する環境
（``Base.metadata.create_all`` で構築された本番など）では実質的に no-op となる。

なお、これらの列は新規構築時には過去のマイグレーションが作成する所有物である
ため、本リビジョンの ``downgrade`` は列を削除せず no-op とする。

Revision ID: f0a1b2c3d4e5
Revises: 4f6a8b2c1d3e
Create Date: 2026-06-11 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "4f6a8b2c1d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """欠落している列を冪等に追加してモデルへ収束させる."""
    op.execute(
        "ALTER TABLE theater_projects "
        "ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE project_members "
        "ADD COLUMN IF NOT EXISTS display_name VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE scripts ADD COLUMN IF NOT EXISTS public_terms TEXT"
    )
    op.execute(
        "ALTER TABLE scripts ADD COLUMN IF NOT EXISTS public_contact VARCHAR(200)"
    )
    op.execute(
        "ALTER TABLE schedule_polls ADD COLUMN IF NOT EXISTS required_roles TEXT"
    )
    op.execute(
        "ALTER TABLE attendance_events "
        "ADD COLUMN IF NOT EXISTS schedule_date TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    """no-op.

    対象列は過去のマイグレーションが作成する所有物であり、本リビジョンは
    既存環境向けに欠落分を補うだけなので、ダウングレードでは何もしない。
    """
