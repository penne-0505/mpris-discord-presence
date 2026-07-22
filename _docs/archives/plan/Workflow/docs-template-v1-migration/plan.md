---
title: docs-driven template v1.0.0 migration plan
status: active
draft_status: n/a
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
related_issues: []
related_prs: []
---

# docs-driven template v1.0.0 migration plan

## Overview

`P=2a2f9ab583b46cb4e1d43ebcbbc33c8d0644ebe1` のclean snapshotを、legacy baseline `B=ebb098e4536d28d834ef8ecbf9686906a5b23d41` からupstream `U=v1.0.0 / f71e9ab20466ea2972158334261f5ae2b2265754` へ三者比較で移行する。cutoffは2026-07-22T11:46:15+09:00、destinationはisolated worktree、並行writerは本taskの担当pathなしである。

## Scope

- validators、fixtures、hooks、paired skills、standards、templates、docs CIをv1.0.0へ統合する。
- shared root docsはproject固有記述を保持してmergeする。
- compatibility PASS後に`docs-template.lock.json`を作成する。

## Non-Goals

- runtime source、installer、service unit、project tests、support境界の変更。
- upstream template自身の`Workflow/lifecycle-self-audit` Plan / Intent / QAの配布。
- semanticな判断を伴わない既存project docsのschema一括変換。
- pushまたはlive service操作。

## Three-way Inventory

### Apply: upstream-owned unmodified

`.agents/skills/{docs-cleanup,docs-prep,implementation-prep,post-implementation,qa-prep,qa-review,test-maintenance}/SKILL.md`、対応する`.claude/skills/**`、`.claude/settings.json`、`.codex/hooks.json`、`_docs/documentation_guide.md`、`_docs/standards/{documentation_guidelines,documentation_operations,quality_assurance}.md`、`_docs/standards/templates/{intent,plan,qa-test-plan,qa-verification}.md`、`_evals/agent-workflows/{README.md,expected-invariants.md}`、既存case群、`_evals/validator-fixtures/{README.md,qa/valid/test-plan.md,qa/valid/verification-pass.md}`、`scripts/{agent-workflow-hook,check-docs,test-agent-workflow-hook,test-agent-workflow-smoke,validate-qa}.mjs`。

### Apply: upstream added

paired `docs-template-migration` skill、agent workflow cases `experimental-baseline` / `misleading-optimization` / `rationale-preserving-change` / `template-version-migration`、intent fixtures、QA v2 invalid fixture、`scripts/validate-intent.mjs`、`docs-template.lock.example.json`。project固有の`docs-template.lock.json`はcompatibility PASS後に追加する。

### Merge: customized shared

`AGENTS.md`、`README.md`、`QUICKSTART.md`、`TODO.md`、`.github/workflows/docs-ci.yml`、`scripts/test-validators.mjs`。project固有文面・tests workflow・security/runtime rulesを優先し、upstreamのwhy-first schema、validator、check command、hook契約だけを統合する。

### Keep: project-only

`.github/workflows/tests.yml`、`.gitignore`、`LICENSE.txt`、`config.example.toml`、`packaging/**`、`pyproject.toml`、`src/**`、`tests/**`、installer scripts、Core areaのarchive / Plan / Intent / QA / guide / referenceを無変更で保持する。

### Exclude: template self meta-work

`_docs/{plan,intent,qa}/Workflow/lifecycle-self-audit/**`はproject運用記録ではないため取り込まない。upstreamの`README.md` / `QUICKSTART.md` / `TODO.md`にあるtemplate-self作業記述もmerge対象外とする。

### Removal

upstream B→Uに削除pathはない。project側にも、完全一致かつ参照ゼロのobsolete template-only fileは確認されなかったため削除しない。

## Requirements

- compatibility validatorを既存project docsへ先に適用し、その後にlockを書く。
- existing INV IDsとhistorical verification evidenceを保持する。
- strict schemaは新規migration docsで採用し、既存Core docsはlegacy-compatibleのまま保持する。
- source/runtime behavior差分が0件であることをdiff reviewする。

## Tasks

1. compatibility filesをimportして既存docsを検証する。
2. standards、paired skills、hooks、CI、shared root docsをmergeする。
3. lockを最終migration writeとして追加する。
4. QA closureを実行し、Planはarchive checklistを満たす場合だけ移送する。

## QA Plan

RiskはHigh。詳細は`_docs/qa/Workflow/docs-template-v1-migration/test-plan.md`を正典とする。

## Deployment / Rollout

単一commitとしてlocal branchへ記録する。pushは行わない。rollbackはcommitのrevertであり、既存checkoutとlive serviceには影響しない。
