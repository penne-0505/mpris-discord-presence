# Case: high-risk-change-verification

## Scenario

認証、権限、データ安全性、migration などに関わる High risk 変更。完了前に verification が必須。

## Initial State

- `TODO.md` に `Risk: High` または `Risk: Critical` のタスクがある。
- Plan / Intent / QA test-plan が存在する。
- `Verification` は `None` または未作成。

## Agent Task

実装後に rollback / recovery / security / data safety の確認を実行または明記し、verification verdict を出す。

## Expected Documents Touched

- `_docs/qa/<Area>/<slug>/verification.md`
- 必要に応じて `_docs/plan/<Area>/<slug>/plan.md`
- 必要に応じて `_docs/intent/<Area>/<slug>/decision.md`
- `TODO.md`

## Expected QA Behavior

- High-risk Checklist が省略されない。
- 未確認リスクは Residual Risks または Deferred / Not Covered に記録される。

## Expected Test / Validator Behavior

- security / data safety / migration に関する validator、test、manual QA、diff review のいずれかが evidence になる。
- `validate-qa` が High-risk Checklist と verdict を検証する。

## Expected Verification

- `PASS` は rollback / recovery / security / data safety の evidence がある場合のみ。
- `PARTIAL` / `FAIL` / `BLOCKED` は残リスクと次アクションが必須。

## Expected TODO.md Behavior

- Verification がないまま完了扱いにしない。
- `FAIL` / `BLOCKED` なら TODO を残す。

## Failure Modes to Watch

- High risk を Medium として扱う。
- rollback や recovery を「不要」で済ませる。
- verification なしで TODO を削除する。
