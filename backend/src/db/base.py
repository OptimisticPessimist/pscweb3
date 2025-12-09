"""SQLAlchemyベースモデル."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全データベースモデルの基底クラス."""

    pass
