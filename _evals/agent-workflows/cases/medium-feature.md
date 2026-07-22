# medium-feature

## Scenario

`Size >= M` の通常機能追加。実装前に Plan が必要で、実装後に intent / guide / reference を更新する。

## Initial State

- `TODO.md` に `Size: M` 以上の Feat または Enhance タスクがある。
- `Plan` は `_docs/plan/<Area>/<slug>/plan.md` を指す。
- 対応 Plan ファイルが存在する。

## Agent Task

Plan の Scope / Non-Goals / Requirements / Test Plan に従って実装し、確定した判断を intent に記録する。

## Expected Documents Touched

- `_docs/plan/<Area>/<slug>/plan.md`
- `_docs/intent/<Area>/<slug>/decision.md`
- `_docs/qa/<Area>/<slug>/test-plan.md`
- `_docs/qa/<Area>/<slug>/verification.md`
- `_docs/guide/<Area>/<slug>/usage.md`
- `_docs/reference/<Area>/<slug>/reference.md`

## Expected QA Behavior

- `Size >= M` requires Plan / Intent / QA.
- QA test-plan is created before or during implementation.

## Expected Decision / Invariant Behavior

- The feature's core design decisions have stable `DEC-*` IDs with `What`, `Why`, and `Change freedom`.
- `INV-*` is added only for a condition that must survive every valid implementation; zero invariants is acceptable.
- User-visible guarantees become ACs and are reflected in guide/reference only after verification.

## Expected Test-plan Behavior

- Test Matrix includes at least one AC row and an INV row only for each applicable invariant.
- Test strategy uses automated tests or validators where practical.

## Expected Verification Behavior

- Verification records commands, manual QA if needed, AC coverage, affected DEC conformance, applicable INV coverage, and verdict.
- TODO is removed only after PASS or accepted PARTIAL.

## Expected TODO.md Behavior

- 実装完了後、対象タスクを `TODO.md` から削除する。
- 追加作業は Backlog に別タスクとして追加する。

## Expected Validation Outcome

- `validate-todo` が Plan path と Area 一致を確認する。
- `validate-frontmatter` が新規 `_docs/` 文書の8必須項目を確認する。
- `validate-doc-links` が references と Markdown リンクの存在を確認する。
- `validate-qa` が QA docs と TODO の Risk / Intent 整合を確認する。

## Failure Modes to Watch

- `Plan` を `_docs/plan/<Area>/<slug>.md` のような非 canonical path に置く。
- intent を作らずに plan を archives へ移す。
- guide / reference に未実装仕様を書く。
