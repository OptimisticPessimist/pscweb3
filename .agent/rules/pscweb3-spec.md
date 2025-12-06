---
trigger: always_on
---

## 技術スタック
- Python 3.13
- Azure（永続的に無料枠を使う）

## Pythonコーディング規約
- PEP 257に従い、Google Styleに則り日本語でコメントを書く。
- Type Hintingは必須。
  - Any型を許容しない。
  - 独自型を積極的に実装する。
- uv + ruff + ty を活用する。
  - ruffはコミット前に必ずチェックする。
  - tyはコミット前に必ずチェックする。