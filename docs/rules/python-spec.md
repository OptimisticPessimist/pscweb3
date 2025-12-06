# Python Coding Standards

## 1. 基本原則 (Basic Principles)
- **Docstrings**: PEP 257に従い、Google Style形式で日本語で記述する。
  - 詳細は `.ruff.toml` の設定（`tool.ruff.lint.ignore` 等）を正とする。
- **Type Hinting**: 型ヒントは必須とする。
  - **No Any**: `Any` 型の使用は原則禁止。
  - **Custom Types**: 独自型（PydanticモデルやTypeAlias）を積極的に実装し、ドメインの表現力を高める。

## 2. ツールチェーン (Tooling)
- **Environment**: `uv` をパッケージ管理・仮想環境管理に使用する。
- **Linter/Formatter**: `ruff` を使用し、コミット前に必ずチェック・修正を行う（`uv run ruff check .` / `uv run ruff format .`）。
- **Type Checker**: `ty` をコミット前に必ず実行し、型整合性を確認する（`uv run ty`）。

## 3. テスト (Testing)
- **Framework**: `pytest` を使用する。
- **TDD**: テスト駆動開発 (TDD) を原則とし、実装コードを書く前にテストを作成する。
- **AAA Pattern**: テストケースは AAA (Arrange, Act, Assert) パターンで記述し、可読性を確保する。
- **Coverage**: コードカバレッジ率 80% 以上を維持する。

## 4. アーキテクチャ (Architecture)
- **Database**: 
  - **SQLAlchemy 2.0**: `Mapped`, `mapped_column` を使用した最新の宣言的スタイルを厳守する。
  - **AsyncIO**: DB操作は全て非同期（`async/await`）で行う。同期的な `Session` は使用しない。
- **Dependency Injection**: FastAPIの `Depends` を活用し、依存関係を注入することでテスト容易性を高める。
- **Layered Structure**: API (Routers), Service (Logic), DB (Models/CRUD), Schemas (Pydantic) の責務を明確に分離する。

## 5. データベース設計 (Database Design)
- **ORM**: SQLAlchemy 2.0を使用し、最新の宣言的スタイルを厳守する。
- **AsyncIO**: DB操作は全て非同期（`async/await`）で行う。同期的な `Session` は使用しない。
- **Dependency Injection**: FastAPIの `Depends` を活用し、依存関係を注入することでテスト容易性を高める。
- **Layered Structure**: API (Routers), Service (Logic), DB (Models/CRUD), Schemas (Pydantic) の責務を明確に分離する。
