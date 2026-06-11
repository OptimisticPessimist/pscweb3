"""Converge legacy migration-built environments with the ORM models.

このリビジョンより前の履歴を適用済みの既存環境は、過去のマイグレーションを
再実行しないため、後付けでモデルに追加された列や型修正が反映されない。本
リビジョンはそれらの乖離を冪等に補い、スキーマをモデルへ収束させる。

(1) 欠落列の追加:
- theater_projects.is_public
- project_members.display_name
- scripts.public_terms
- scripts.public_contact
- schedule_polls.required_roles
- attendance_events.schedule_date

すべて ``ADD COLUMN IF NOT EXISTS`` を用いるため、列が既に存在する環境
（``Base.metadata.create_all`` で構築された本番など）では実質的に no-op となる。

(2) タイムスタンプ型の収束 (timezone-naive -> timezone-aware):
モデルの datetime 列はすべて ``DateTime(timezone=True)`` だが、旧マイグレーション
や手動SQL（例: ``migrations/add_schedule_date_to_attendance.sql`` の
``schedule_date TIMESTAMP``）が ``TIMESTAMP WITHOUT TIME ZONE`` で作成した列が
既存環境に残る。これらはUTC以外の接続タイムゾーンで日時がずれるため、
``TIMESTAMP WITH TIME ZONE`` へ変換する。既存の naive 値はアプリが UTC
(``datetime.now(UTC)``) で書き込むため ``AT TIME ZONE 'UTC'`` で解釈する。

変換は ``data_type = 'timestamp without time zone'`` の列のみを対象とする。
既に timezone-aware な列（本番など）に ``USING ... AT TIME ZONE 'UTC'`` を
適用すると二重変換でデータが破損するため、対象を厳密に絞り冪等性を担保する。

なお、これらの列・型は新規構築時には過去のマイグレーションが作成する所有物
であるため、本リビジョンの ``downgrade`` は何もしない（no-op）。

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
    """欠落列の追加とタイムスタンプ型の収束を冪等に行う."""
    # (1) 欠落している列を冪等に追加してモデルへ収束させる。
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

    # (2) timezone-naive なタイムスタンプ列を timezone-aware へ収束させる。
    #     対象を data_type = 'timestamp without time zone' に厳密に絞ることで、
    #     既に timezone-aware な列には触れず（= 本番では no-op）冪等にする。
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN
                SELECT c.table_name, c.column_name
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema
                 AND t.table_name = c.table_name
                WHERE c.table_schema = 'public'
                  AND t.table_type = 'BASE TABLE'
                  AND c.data_type = 'timestamp without time zone'
            LOOP
                EXECUTE format(
                    'ALTER TABLE public.%I ALTER COLUMN %I TYPE '
                    'TIMESTAMP WITH TIME ZONE USING %I AT TIME ZONE ''UTC''',
                    r.table_name, r.column_name, r.column_name
                );
            END LOOP;
        END
        $$;
        """
    )


def downgrade() -> None:
    """no-op.

    対象の列・型は過去のマイグレーションが作成する所有物であり、本リビジョンは
    既存環境向けに乖離を補うだけなので、ダウングレードでは何もしない。
    """
