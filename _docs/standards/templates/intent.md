---
title: Intent / Decision Title
status: active  # allowed: proposed | active | superseded | obsolete
draft_status: n/a  # allowed: idea | exploring | paused | n/a
intent_schema: 2
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
references:
  - "_docs/plan/<Area>/<slug>/plan.md"
  - "_docs/qa/<Area>/<slug>/test-plan.md"
related_issues: []
related_prs: []
---

<!-- Canonical path: _docs/intent/<Area>/<slug>/decision.md -->
<!-- 設計判断の背景と根拠を簡潔に記録。関連する plan / QA / draft / survey / archive を references に追記してください。intent は恒久記録であり archive しません。 -->

## Context
- 背景と課題

## Decisions

### DEC-001: Decision title

- **What**: 採用した方針・設計
- **Why**: 解決する問題、守る性質、避ける失敗との因果
- **Change freedom**: Why を保つ限り変更できる実装方式・値・構造
<!-- Optional fields: `- **Why not**: 一見妥当に見える不採用案と、その案では目的を満たせない理由`, `- **Revisit when**: 再検討を可能にする証拠・条件` -->

## Consequences / Impact
- 影響範囲（API/データ/セキュリティ/パフォーマンス など）

## Quality Implications
- この判断が守るべき品質条件
- 破ると起きる回帰・運用リスク
- QA test-plan で確認すべき観点

## Intent-derived Invariants
<!-- 任意。active decision 下で実装方式が変わっても破れない結果だけを書く。比較条件、現行値、migration 中だけの保全条件を INV にしない。0 件なら None。 -->
None
<!-- 必要な場合の形式: `- INV-001 (from DEC-001): 実装方式が変わっても破れない結果` -->

## Enforced in (optional)
<!-- 任意。各 DEC / INV が体現・enforce されている場所への back-reference。code 起点だけでなく intent 起点でも実装箇所へ辿れるようにする。 -->
None

## Rollback / Follow-ups
- ロールバック方針や追加フォロー項目
