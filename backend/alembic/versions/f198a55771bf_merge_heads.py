"""Alembicマイグレーションスクリプトテンプレート.

Revision ID: f198a55771bf
Revises: 0209794dca2b, e3f4a5b6c7d8
Create Date: 2025-12-12 22:17:01.893992

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "f198a55771bf"
down_revision: str | None = ("0209794dca2b", "e3f4a5b6c7d8")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """アップグレードマイグレーション."""
    pass


def downgrade() -> None:
    """ダウングレードマイグレーション."""
    pass
