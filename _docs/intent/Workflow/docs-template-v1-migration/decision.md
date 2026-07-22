---
title: docs-driven template provenance migration
status: active
draft_status: n/a
intent_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/archives/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/verification.md"
related_issues: []
related_prs: []
---

# docs-driven template provenance migration

## Context

projectはpre-v1.0.0 templateをcustomizeしており、provenance lockを持たない。blind replacementはruntime契約とproject docsを失わせ、schema一括変換は既存decisionの意味を変える可能性がある。

## Decisions

### DEC-001: provenance固定の三者比較を使う

- **What**: B / U / Pをfull SHAで固定し、pathごとの分類と解決を行う。
- **Why**: moving branchや見た目の一致からbaselineを推測せず、upstream変更とproject customizationを区別するため。
- **Change freedom**: 同じprovenanceと分類を再現できる限り、inventoryの表現や統合toolは変更できる。

### DEC-002: compatibilityとstrict schemaを分離する

- **What**: v1.0.0をlegacy-compatibleに統合し、新規migration recordsだけschema v2で作る。既存Core docsは意味の再検討なしに一括変換しない。
- **Why**: template revision adoptionとproject decisionsのsemantic rewriteを同一作業にすると、validator通過のためだけにdurable recordsの意味が変わるため。
- **Change freedom**: 後続のowner-approved taskで各Core decisionをsemantic reviewし、v2へ移行できる。

### DEC-003: project runtime contractを移行対象外にする

- **What**: source、installer、service unit、project tests、Arch系＋公式Discord support境界、privacy/security ruleを保持する。
- **Why**: docs workflow migrationがproduct behaviorや公開support claimを変更することを防ぐため。
- **Change freedom**: project taskとして別途Plan / Intent / QAを用意した場合は変更できる。

### DEC-004: imported lifecycle guardrailの監査境界をproject内に保持する

- **What**: per-prompt contextは短い仮説・反証・scope確認に限定し、非局所影響と恒久性の詳細監査はwrite boundaryへ置く。どちらもscope拡張の権限にはしない。
- **Why**: 毎promptに詳細監査を重ねると対話と作業のsignal-to-noiseが下がる一方、write前の監査を省くとcaller、data flow、operations、future maintenanceへの影響を見落とすため。削除対象のupstream self-audit recordではなく、導入project内の到達可能なdecisionとして根拠を残す。
- **Change freedom**: 短いprompt再確認、write前の非局所監査、scope非拡張という役割分担を保つ限り、文面・event・実装構造は変更できる。

## Consequences / Impact

v1.0.0のwhy-first workflowとprovenance lockを利用できる。既存Core recordsはlegacy schemaとして有効であり、strict v2全面移行は完了扱いに含めない。

## Quality Implications

blind replacement、branch mixing、premature lock、bulk schema editをdiffとfixturesで検出する。runtime source差分は0件を要求する。
imported lifecycle hookは、DEC-004の境界をhook testsとsmoke testsで確認する。

## Intent-derived Invariants

- INV-001 (from DEC-001): lockは実際に統合・検証したv1.0.0 full SHAだけを指す。
- INV-002 (from DEC-003): migration commitは`src/**`、installer、service unit、project testsの内容を変更しない。

## Enforced in (optional)

- INV-001: `docs-template.lock.json`、QA provenance review。
- INV-002: final path diffとproject regression checks。
- DEC-004: `scripts/agent-workflow-hook.mjs`、hook unit / smoke tests。

## Rollback / Follow-ups

local commitをrevertできる。既存Core docsのstrict schema v2化は個別のsemantic reviewが必要になった時点で別taskとする。
