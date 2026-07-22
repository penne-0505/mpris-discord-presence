---
title: Plan Title
status: proposed  # allowed: proposed | active | superseded | obsolete
draft_status: n/a  # allowed: idea | exploring | paused | n/a
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
references:
  - "_docs/intent/<Area>/<slug>/decision.md"
  - "_docs/qa/<Area>/<slug>/test-plan.md"
related_issues: []
related_prs: []
---

<!-- Canonical path: _docs/plan/<Area>/<slug>/plan.md -->
<!-- 合意済み仕様のみを記載。Scope / Non-Goals / QA Plan を網羅し、破壊的変更時は status や updated_at を必ず更新してください。 -->
<!-- Size >= M では _docs/qa/<Area>/<slug>/test-plan.md も作成してください。 -->

## Overview
- 計画の概要

## Scope
- 実装する機能範囲
- 影響範囲

## Non-Goals
- 対象外とする事項

## Requirements
- **Functional**: 機能要件
- **Non-Functional**: 非機能要件

## Tasks
- 実装タスク一覧

## QA Plan
- QA document: `_docs/qa/<Area>/<slug>/test-plan.md`
- Risk level: Low | Medium | High | Critical
- Test strategy:
  - Unit:
  - Integration:
  - E2E:
  - Manual QA:
  - Validator / static check:
- Acceptance criteria と、該当する intent-derived invariant をどの確認手段に紐づけるか。
- 実装が影響する `DEC-xxx` と、その `Why` / `Change freedom` の review 方針。
- `Size >= M` または `Risk >= Medium` の場合、実装前または実装中に QA test-plan を作成する。
- Risk High / Critical の場合は rollback / recovery / data safety / security の確認観点を含める。

## Deployment / Rollout
- リリース手順・監視・ロールバック方針
