---
title: Reference Title
status: active  # allowed: proposed | active | superseded | obsolete
draft_status: n/a  # allowed: idea | exploring | paused | n/a
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
references:
  - "_docs/intent/<Area>/<slug>/decision.md"
  - "_docs/qa/<Area>/<slug>/verification.md"
related_issues: []
related_prs: []
---

<!-- Canonical path: _docs/reference/<Area>/<slug>/reference.md -->
<!-- 実装済み API/仕様のみ。パラメータ・戻り値・例外・例を網羅してください。 -->

## Overview
- 対象API/モジュールの概要

## API

### Endpoint or Class

- **Summary**: 説明
- **Parameters**: name (type) — 説明
- **Returns**: 型と意味
- **Errors**: 例外・エラーコード
- **Examples**: 代表的な使用例

## Notes
- 補足事項やバージョン差分

## Verification
- 関連 QA: `_docs/qa/<Area>/<slug>/test-plan.md`
- 検証証跡: `_docs/qa/<Area>/<slug>/verification.md`
- API / 仕様の保証範囲が変わる場合は、verification の verdict と残リスクを参照する
