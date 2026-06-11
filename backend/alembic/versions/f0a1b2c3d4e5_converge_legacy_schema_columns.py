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

対象はモデルが ``DateTime(timezone=True)`` で定義する既知のアプリ管理列に
明示的に限定する。``public`` スキーマを他サービスや手動作成テーブルと共有する
環境で、アプリ管理外テーブルの naive timestamp を巻き込んだり（ローカル時刻を
UTC と誤解釈する／マイグレーションロールが所有しないテーブルで ``ALTER`` が
失敗してアップグレード全体がロールバックする）といった事故を避けるため。

加えて、変換は ``data_type = 'timestamp without time zone'`` の列のみに適用する。
既に timezone-aware な列（本番など）に ``USING ... AT TIME ZONE 'UTC'`` を
適用すると二重変換でデータが破損するため、対象を厳密に絞り冪等性を担保する。
列が存在しない環境ではスキップする。

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
    #     対象はモデルが DateTime(timezone=True) で定義する既知の列に限定し
    #     （アプリ管理外テーブルを巻き込まない）、かつ実際に naive な列のみを
    #     変換する（既に tz-aware なら no-op、列が無ければスキップ）。
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
            col_type text;
        BEGIN
            FOR r IN
                SELECT * FROM (VALUES
                    ('users', 'created_at'),
                    ('theater_projects', 'created_at'),
                    ('attendance_events', 'schedule_date'),
                    ('attendance_events', 'deadline'),
                    ('attendance_events', 'reminder_1_sent_at'),
                    ('attendance_events', 'reminder_2_sent_at'),
                    ('attendance_events', 'reminder_3_sent_at'),
                    ('attendance_events', 'created_at'),
                    ('audit_logs', 'created_at'),
                    ('milestones', 'start_date'),
                    ('milestones', 'end_date'),
                    ('project_invitations', 'expires_at'),
                    ('project_invitations', 'created_at'),
                    ('project_members', 'joined_at'),
                    ('schedule_polls', 'deadline'),
                    ('schedule_polls', 'reminder_sent_at'),
                    ('schedule_polls', 'created_at'),
                    ('scripts', 'uploaded_at'),
                    ('rehearsal_schedules', 'created_at'),
                    ('reservations', 'reminder_sent_at'),
                    ('reservations', 'created_at'),
                    ('scene_charts', 'created_at'),
                    ('scene_charts', 'updated_at'),
                    ('schedule_poll_candidates', 'start_datetime'),
                    ('schedule_poll_candidates', 'end_datetime'),
                    ('rehearsals', 'date'),
                    ('schedule_poll_answers', 'updated_at')
                ) AS t(table_name, column_name)
            LOOP
                SELECT data_type INTO col_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = r.table_name
                  AND column_name = r.column_name;

                IF col_type = 'timestamp without time zone' THEN
                    EXECUTE format(
                        'ALTER TABLE public.%I ALTER COLUMN %I TYPE '
                        'TIMESTAMP WITH TIME ZONE USING %I AT TIME ZONE ''UTC''',
                        r.table_name, r.column_name, r.column_name
                    );
                END IF;
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
