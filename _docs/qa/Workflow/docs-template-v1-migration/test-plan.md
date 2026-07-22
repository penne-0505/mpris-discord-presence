---
title: "QA Test Plan: docs-driven template v1.0.0 migration"
status: active
draft_status: n/a
qa_status: planned
risk: High
qa_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/archives/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/verification.md"
related_issues: []
related_prs: []
---

# QA Test Plan: docs-driven template v1.0.0 migration

## Source of Intent

- TODO: `Workflow-Chore-12`
- Plan: `_docs/archives/plan/Workflow/docs-template-v1-migration/plan.md`
- Intent: `_docs/intent/Workflow/docs-template-v1-migration/decision.md`

## Quality Goal

project customizationとruntime behaviorを保持し、v1.0.0 workflowをprovenance付きで再現可能に統合する。

## Acceptance Criteria

- AC-001: provenanceとinventoryが明示される。
- AC-002: workflow assetsがpath-by-pathで統合される。
- AC-003: project contractが保持される。
- AC-004: compatibilityとstrict schema判定が分離される。
- AC-005: closure checksがPASSしruntime source差分がない。

## Decision Review Scope

- DEC-001: B / U / P、branch、lockが一致する。
- DEC-002: legacy Core docsを機械的一括変換していない。
- DEC-003: runtime/support/security customizationが保持される。
- DEC-004: per-prompt / write auditの役割分担とscope非拡張がproject内decisionへtraceされる。

## Intent-derived Invariants

- INV-001: lockは統合済みv1.0.0 full SHAだけを指す。
- INV-002: runtime source・installer・service unit・project testsは無変更である。

## Risk Assessment

- Risk level: High
- Risk rationale: validator、CI、migration、agent workflowを同時に更新する。
- Regression risk: project customizationの上書き、旧docs拒否、hooks誤作動。
- Data safety risk: live data操作なし。
- Security / privacy risk: metadata loggingとcredential boundaryを保持する。
- UX risk: docs checkとcontributor workflowの互換性。
- Agent misbehavior risk: branch mixing、blind replacement、premature lock、bulk schema edit、template meta-work import。

## Test Strategy

- Unit: validator / hook fixtures。
- Integration: `check-docs.sh`、project unittest、installer dry integration test。
- E2E: live service操作はscope外。
- Manual QA: inventory、lock、support/security文面、diffをreviewする。
- Validator / static check: Deno fmt、markdownlint、paired-skill cmp、diff check。
- Diff review: runtime/project-only pathのblob不変を確認する。

## Test Matrix

| ID | Source | Requirement / Optional Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | provenance | review | lock、Plan | B/U/Pが一致 | planned |
| AC-002 | TODO | workflow integration | validators | `./scripts/check-docs.sh` | PASS | planned |
| AC-003 | TODO | customization preservation | diff + tests | git diff、project tests | behavior path差分なし | planned |
| AC-004 | TODO | staged schema boundary | validator + review | intent/QA validators | legacyとv2が共存 | planned |
| AC-005 | TODO | closure | regression suite | documented commands | 全PASS | planned |
| INV-001 | intent | lock accuracy | static review | `git rev-parse v1.0.0^{}` | SHA一致 | planned |
| INV-002 | intent | runtime paths unchanged | diff review | `git diff -- src tests scripts/install-user-service.sh packaging` | expected zero | planned |

## Manual QA Checklist

- [ ] supportとprivacy/security boundaryが保持される。
- [ ] template self meta-workが含まれない。
- [ ] existing checkoutとlive serviceを操作していない。

## Regression Checklist

- [ ] baseline failureとの差分が説明される。
- [ ] hooksとpaired skillsが同期する。
- [ ] project testsとpackage buildがPASSする。

## High-risk Checklist

- [x] Rollback or recovery path is documented.
- [x] Data safety has been checked.
- [x] Security / privacy implications have been checked.
- [x] Failure mode is understood.

## Out of Scope

- live Discord/service QA、push、既存Core docsのschema全面変換。

## Open Questions

- None
