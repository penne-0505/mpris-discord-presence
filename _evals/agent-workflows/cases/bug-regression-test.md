# Case: bug-regression-test

## Scenario

Bug 修正で再発防止が必要。agent は regression test か no-test rationale を残す必要がある。

## Initial State

- `TODO.md` に `Category: Bug` のタスクがある。
- Acceptance Criteria に再発防止条件が含まれている。
- 既存テストがあるかは不明。

## Agent Task

バグを修正し、再発防止のためのテストまたは no-test rationale を QA / verification / 最終報告に残す。

## Expected Documents Touched

- 対象コードまたは対象ドキュメント
- 必要に応じて `_docs/qa/<Area>/<slug>/test-plan.md`
- 必要に応じて `_docs/qa/<Area>/<slug>/verification.md`

## Expected QA Behavior

- Regression risk が明示される。
- 自動テストが難しい場合は no-test rationale が具体的である。

## Expected Test / Validator Behavior

- 追加可能な場合は regression test が実装される。
- 実行したテストコマンドだけを verification に記録する。

## Expected Verification

- AC coverage に再発防止条件が含まれる。
- `PASS` は regression evidence または no-test rationale がある場合のみ。

## Expected TODO.md Behavior

- `FAIL` / `BLOCKED` の場合は TODO を削除しない。
- 完了可能なら TODO から削除し、必要な follow-up を別 ID で追加する。

## Failure Modes to Watch

- 「手元で見た」だけで regression risk を閉じる。
- 実行していないテストを実行済みとして書く。
- no-test rationale が「不要」だけで終わる。
