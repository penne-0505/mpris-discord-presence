---
title: Intent / Decision Title
status: active  # allowed: proposed | active | superseded | obsolete
draft_status: n/a  # allowed: idea | exploring | paused | n/a
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

## Decision
- 採用した方針・設計

## Alternatives
- 検討した代替案と不採用理由

## Rationale
- 判断根拠・トレードオフ

## Consequences / Impact
- 影響範囲（API/データ/セキュリティ/パフォーマンス など）

## Quality Implications
- この判断が守るべき品質条件
- 破ると起きる回帰・運用リスク
- QA test-plan で確認すべき観点

## Intent-derived Invariants
<!-- 安定 ID を振り、コードから一行で引用できる粒度・断定形で書く。非自明なコードはこの ID を `// intent: INV-00X (<Area>/<slug>) — ...` でアンカーできる。詳細は quality_assurance.md の intent ↔ code traceability を参照。 -->
- INV-001:
- INV-002:
- INV-003:

## Enforced in (optional)
<!-- 任意。各 INV が体現・enforce されている場所への back-reference。code 起点だけでなく intent 起点でも実装箇所へ辿れるようにする。 -->
- INV-001:

## Rollback / Follow-ups
- ロールバック方針や追加フォロー項目
